import tkinter as tk
from tkinter import ttk, messagebox, simpledialog, filedialog
import psycopg2
from psycopg2.extras import RealDictCursor
import hashlib
from datetime import datetime
import os
# Coneccion con la base de datos
DB_NAME = "inventario_discos3"
DB_USER = "postgres"
DB_PASS = "Soysuficiente91*" 
DB_HOST = "localhost"
DB_PORT = 5432

#funcion hashpassword (Encapsulamiento de informacion sensible)
def hash_password(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()

#funcion contrasena_por_default_del_usuario (Encapsulamiento de informacion sensible)
def contrasena_por_default_del_usuario(nombre_usuario: str) -> str:
    primer_nombre = (nombre_usuario.strip().split()[0] if nombre_usuario else "").lower()
    return primer_nombre + "123"

#funcion quicksort (Ordenamiento optimo para grandes listas desordenadas log n, mediante un pivote)
def quicksort(lista, key_fn, reverse=False):
    if len(lista) <= 1:
        return lista
    pivote = lista[len(lista)//2]
    k = key_fn(pivote)
    menores = [x for x in lista if key_fn(x) < k]
    iguales = [x for x in lista if key_fn(x) == k]
    mayores = [x for x in lista if key_fn(x) > k]
    res = quicksort(menores, key_fn) + iguales + quicksort(mayores, key_fn)
    return list(reversed(res)) if reverse else res

# Capa de base de datos
class Database:
    _instance = None
#Metodo __new__(cls): aplicamos singleton. Separado el espacio en memoria para la DB
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._conn = None
        return cls._instance
    
#Metodo coneccion(self): coneccion con base de datos
    def coneccion(self):
        if self._conn is None or self._conn.closed:
            self._conn = psycopg2.connect(
                dbname=DB_NAME,
                user=DB_USER,
                password=DB_PASS,
                host=DB_HOST,
                port=DB_PORT
            )
            self._conn.autocommit = True
        return self._conn
    
#Metodo cursor(self): devuelve resultados en forma descriptiva
    def cursor(self):
        return self.coneccion().cursor(cursor_factory=RealDictCursor)
    
#Metodo commit(self): commit de cambios desde la app hacia postgres
    def commit(self):
        if self._conn:
            self._conn.commit()

# Capa de Autenticación (abstraccion)
class GestorAutenticacion:
    def __init__(self):
        self.db = Database()
        self.aseguramiento_perfiles()
        self.aseguramiento_usuarios_default()
        self.creacion_password_nuevas()  
# Asegura que existan 1=Gerencia, 2=Bodega, 3=Vendedores en la DB
    def aseguramiento_perfiles(self):
        cur = self.db.cursor()
        cur.execute("""
            INSERT INTO perfil (id_perfil, nombre_perfil) VALUES
            (1,'Gerencia') ON CONFLICT (id_perfil) DO NOTHING;
        """)
        cur.execute("""
            INSERT INTO perfil (id_perfil, nombre_perfil) VALUES
            (2,'Bodega') ON CONFLICT (id_perfil) DO NOTHING;
        """)
        cur.execute("""
            INSERT INTO perfil (id_perfil, nombre_perfil) VALUES
            (3,'Vendedores') ON CONFLICT (id_perfil) DO NOTHING;
        """)
# Asegura que existan los usuarios 1 Gerencia, 2 Bodega, 3 Vendedores si no existen en la DB
    def aseguramiento_usuarios_default(self):
        cur = self.db.cursor()
        defaults = [
            ("Danni Brito", "danni.gerente@test.com", 1),
            ("Jose Galarraga", "jose.bodega@test.com", 2),
            ("Cristian Montero", "cristian.bodega@test.com", 2),
            ("Billy Garzon", "billy.vendedor@test.com", 3),
            ("Fabian Vega", "fabian.vendedor@test.com", 3),
            ("Paul Pareja", "paul.vendedor@test.com", 3),
        ]
        for nombre, correo, perfil in defaults:
            cur.execute("SELECT id_usuario FROM usuario WHERE nombre_usuario=%s", (nombre,))
            row = cur.fetchone()
            if not row:
                cur.execute(
                    "INSERT INTO usuario (nombre_usuario, correo, id_perfil1) VALUES (%s,%s,%s) RETURNING id_usuario",
                    (nombre, correo, perfil)
                )
                new_id = cur.fetchone()["id_usuario"]
#Creacion de la contrasena por default (herencia)
                pwd = contrasena_por_default_del_usuario(nombre)
                cur.execute(
                    "INSERT INTO auth (id_usuario, password_hash) VALUES (%s,%s)",
                    (new_id, hash_password(pwd))
                )
#Creacion de la contrasena por default (a usuarios nuevos)
    def creacion_password_nuevas(self):
        cur = self.db.cursor()
        cur.execute(
            """
            SELECT u.id_usuario, u.nombre_usuario
            FROM usuario u
            LEFT JOIN auth a ON a.id_usuario = u.id_usuario
            WHERE a.id_usuario IS NULL
            """
        )
        rows = cur.fetchall()
        for r in rows:
            pwd = contrasena_por_default_del_usuario(r["nombre_usuario"])
            cur.execute(
                "INSERT INTO auth (id_usuario, password_hash) VALUES (%s,%s)",
                (r["id_usuario"], hash_password(pwd))
            )

    def autenticacion(self, nombre_usuario: str, password: str):
        # Sincroniza por si hay usuarios nuevos recién agregados
        self.creacion_password_nuevas()
        cur = self.db.cursor()
        cur.execute(
            """
            SELECT u.id_usuario, u.nombre_usuario, u.id_perfil1, p.nombre_perfil, a.password_hash
            FROM usuario u
            JOIN perfil p ON p.id_perfil = u.id_perfil1
            JOIN auth a   ON a.id_usuario = u.id_usuario
            WHERE u.nombre_usuario = %s
            """,
            (nombre_usuario,)
        )
        row = cur.fetchone()
        if row and row["password_hash"] == hash_password(password):
            return {
                "id": row["id_usuario"],
                "nombre": row["nombre_usuario"],
                "perfil": row["id_perfil1"],
                "perfil_nombre": row["nombre_perfil"],
            }
        return None
# Crear nuevo usuario
    def anadir_usuario(self, nombre_usuario: str, correo: str, perfil: int, password: str | None = None):
        cur = self.db.cursor()
        try:
            cur.execute(
                "INSERT INTO usuario (nombre_usuario, correo, id_perfil1) VALUES (%s,%s,%s) RETURNING id_usuario",
                (nombre_usuario, correo, perfil)
            )
            new_id = cur.fetchone()["id_usuario"]
            pwd = password or contrasena_por_default_del_usuario(nombre_usuario)
            cur.execute(
                "INSERT INTO auth (id_usuario, password_hash) VALUES (%s,%s)",
                (new_id, hash_password(pwd))
            )
            messagebox.showinfo("Usuario creado", f"Usuario: {nombre_usuario} Contraseña: {pwd}")
            return True
        except Exception as e:
            messagebox.showerror("Error", f"No se pudo crear el usuario: {e}")
            return False
# Eliminar usuario
    def eliminar_usuario(self, nombre_usuario: str):
        cur = self.db.cursor()
        try:
            cur.execute("SELECT id_usuario FROM usuario WHERE nombre_usuario=%s", (nombre_usuario,))
            row = cur.fetchone()
            if not row:
                messagebox.showwarning("Atención", "Usuario no encontrado")
                return False
            uid = row["id_usuario"]
            cur.execute("DELETE FROM auth WHERE id_usuario=%s", (uid,))
            cur.execute("DELETE FROM usuario WHERE id_usuario=%s", (uid,))
            messagebox.showinfo("Listo", "Usuario eliminado con exito")
            return True
        except Exception as e:
            messagebox.showerror("Error", f"No se pudo eliminar: {e}")
            return False

# Capa Repositorio de Discos
class RepositorioDiscos:
    def __init__(self):
        self.db = Database()
#Ordena por id_disco 
    def ordenar_todo(self):
        cur = self.db.cursor()
        cur.execute("SELECT * FROM disco_musica ORDER BY id_disco")
        return cur.fetchall()
#Ordena por id_disco 
    def buscar(self, texto: str):
        cur = self.db.cursor()
        coincidencia = f"%{texto.lower()}%"
        cur.execute(
            """
            SELECT * FROM disco_musica
            WHERE LOWER(nombre_disco) LIKE %s
               OR LOWER(artista) LIKE %s
               OR LOWER(genero) LIKE %s
            ORDER BY id_disco
            """,
            (coincidencia, coincidencia, coincidencia)
        )
        return cur.fetchall()
#obtener disco por id_disco 
    def obtener_por_id_disco(self, id_disco: int):
        cur = self.db.cursor()
        cur.execute("SELECT * FROM disco_musica WHERE id_disco=%s", (id_disco,))
        return cur.fetchone()

    def anadir(self, nombre, precio, artista, fecha, peso_mb, genero, stock=0):
        cur = self.db.cursor()
        cur.execute(
            """
            INSERT INTO disco_musica (nombre_disco, precio, artista, fecha_lanzamiento, peso_mb, genero, stock)
            VALUES (%s,%s,%s,%s,%s,%s,%s) RETURNING id_disco
            """,
            (nombre, precio, artista, fecha, peso_mb, genero, stock)
        )
        return cur.fetchone()["id_disco"]

    def actualizar(self, id_disco, nombre, precio, artista, fecha, peso_mb, genero, stock):
        cur = self.db.cursor()
        cur.execute(
            """
            UPDATE disco_musica
            SET nombre_disco=%s, precio=%s, artista=%s, fecha_lanzamiento=%s, peso_mb=%s, genero=%s, stock=%s
            WHERE id_disco=%s
            """,
            (nombre, precio, artista, fecha, peso_mb, genero, stock, id_disco)
        )

    def eliminar(self, id_disco):
        cur = self.db.cursor()
        cur.execute("DELETE FROM disco_musica WHERE id_disco=%s", (id_disco,))

    def anadir_stock(self, id_disco: int, cantidad: int, id_usuario: int):
        cur = self.db.cursor()
        cur.execute("UPDATE disco_musica SET stock = stock + %s WHERE id_disco=%s RETURNING stock", (cantidad, id_disco))
        nuevo = cur.fetchone()["stock"]
        # Registrar movimiento de inventario
        cur.execute(
            "INSERT INTO movimiento_inventario (id_usuario, id_disco, tipo, cantidad) VALUES (%s,%s,'entrada',%s)",
            (id_usuario, id_disco, cantidad)
        )
        return nuevo
# Capa de Logger de Actividades (archivo .txt descargable)
class RegistroActividades:
    def __init__(self, usuario: str):
        self.usuario = usuario
        self.log_path = "Registro_de_actividades.txt"

    def log(self, accion: str, detalle: str):
        t = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        line = f"[{t}] Usuario: {self.usuario} | Acción: {accion} | Detalles: {detalle}\n"
        with open(self.log_path, "a", encoding="utf-8") as f:
            f.write(line)

    def exportar_log(self):
        carpeta = r"\\192.168.23.128\Bodega"
        os.makedirs(carpeta, exist_ok=True) 

        nombre_archivo = f"registro_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
        ruta = os.path.join(carpeta, nombre_archivo)

        try:
            with open(self.log_path, "r", encoding="utf-8") as fsrc, open(ruta, "w", encoding="utf-8") as fdst:
                fdst.write(fsrc.read())
            messagebox.showinfo("Listo", f"Log guardado en:\n{ruta}")
        except Exception as e:
            messagebox.showerror("Error", str(e))

# Capa de Editor de Discos (Top Level) ventana secundaria
# Hereda tk.Toplevel de la libreria Tkinter
class EditorDisco(tk.Toplevel):
    def __init__(self, master, row=None):
        super().__init__(master)
        self.title("Editar Disco" if row else "Agregar Disco")
        self.result = None

        Etiquetas = [
            ("Nombre", 0), ("Precio", 1), ("Artista", 2), ("Fecha (YYYY-MM-DD)", 3),
            ("Peso (MB)", 4), ("Género", 5), ("Stock", 6)
        ]
        for text, r in Etiquetas:
            ttk.Label(self, text=text).grid(row=r, column=0, sticky="e", padx=6, pady=4)

        self.e_nombre = ttk.Entry(self); self.e_nombre.grid(row=0, column=1, padx=6, pady=4)
        self.e_precio = ttk.Entry(self); self.e_precio.grid(row=1, column=1, padx=6, pady=4)
        self.e_artista = ttk.Entry(self); self.e_artista.grid(row=2, column=1, padx=6, pady=4)
        self.e_fecha = ttk.Entry(self); self.e_fecha.grid(row=3, column=1, padx=6, pady=4)
        self.e_peso  = ttk.Entry(self); self.e_peso.grid(row=4, column=1, padx=6, pady=4)
        self.e_genero= ttk.Entry(self); self.e_genero.grid(row=5, column=1, padx=6, pady=4)
        self.e_stock = ttk.Entry(self); self.e_stock.grid(row=6, column=1, padx=6, pady=4)

        if row:
            self.e_nombre.insert(0, row["nombre_disco"])
            self.e_precio.insert(0, str(row["precio"]))
            self.e_artista.insert(0, row["artista"])
            self.e_fecha.insert(0, str(row["fecha_lanzamiento"]))
            self.e_peso.insert(0, str(row["peso_mb"]))
            self.e_genero.insert(0, row["genero"] or "")
            self.e_stock.insert(0, str(row["stock"]))

        ttk.Button(self, text="Guardar", command=self.grabar).grid(row=7, column=0, columnspan=2, pady=8)

    def grabar(self):
        try:
            nombre = self.e_nombre.get().strip()
            precio = float(self.e_precio.get()) if self.e_precio.get() else None
            artista= self.e_artista.get().strip()
            fecha  = self.e_fecha.get().strip() or None
            peso   = float(self.e_peso.get()) if self.e_peso.get() else None
            genero = self.e_genero.get().strip() or None
            stock  = int(self.e_stock.get() or 0)
            if not nombre:
                messagebox.showwarning("Validación", "Nombre requerido")
                return
            self.result = (nombre, precio, artista, fecha, peso, genero, stock)
            self.destroy()
        except Exception as e:
            messagebox.showerror("Error", f"Datos inválidos: {e}")

# Capa de Aplicación Principal (UI)
class MainApp:
    def __init__(self, user):
        self.user = user
        self.db = Database()
        self.auth = GestorAutenticacion()
        self.repo = RepositorioDiscos()
        self.logger = RegistroActividades(user["nombre"])
#creacion de ventana principal 
        self.root = tk.Tk()
        self.root.title("FloydMusic — Gestor de Inventario")
        self.root.geometry("1100x640")

#barra superior
        top = ttk.Frame(self.root, padding=6)
        top.pack(side="top", fill="x")
        ttk.Label(top, text=f"Bienvenido: {user['nombre']} ({user['perfil_nombre']})", font=("Arial", 12, "bold")).pack(side="left")
        ttk.Button(top, text="Generar Log", command=self.on_export_log).pack(side="right", padx=4)
        ttk.Button(top, text="Cerrar Sesión", command=self.logout).pack(side="right", padx=4)
        if user["perfil"] == 1:
            ttk.Button(top, text="Gestionar Usuarios", command=self.abrir_admin_usuarios).pack(side="right", padx=4)

#Controles de busqueda y ordenamiento
        ctrl = ttk.Frame(self.root, padding=6)
        ctrl.pack(side="top", fill="x")
        ttk.Label(ctrl, text="Buscar:").pack(side="left")
        self.var_busqueda = tk.StringVar()
        ttk.Entry(ctrl, textvariable=self.var_busqueda, width=40).pack(side="left", padx=4)
        ttk.Button(ctrl, text="Ir", command=self.en_busqueda).pack(side="left")

        ttk.Label(ctrl, text=" Ordenar por:").pack(side="left", padx=(12, 4))
        self.var_field = tk.StringVar(value="id")
        self.cbo_field = ttk.Combobox(ctrl, width=12, state="readonly",
                                      values=["id", "nombre", "artista", "genero", "stock"],
                                      textvariable=self.var_field)
        self.cbo_field.pack(side="left")
        self.var_desc = tk.BooleanVar(value=False)
        ttk.Checkbutton(ctrl, text="Desc", variable=self.var_desc).pack(side="left", padx=4)
        ttk.Button(ctrl, text="Ordenar (QuickSort)", command=self.en_ordenamiento).pack(side="left", padx=8)

#TREEVIEW (tabla central)
        cols = ("id", "nombre", "precio", "artista", "fecha", "peso", "genero", "stock")
        self.tree = ttk.Treeview(self.root, columns=cols, show="headings")
        for c in cols:
            self.tree.heading(c, text=c.title())
            self.tree.column(c, width=120 if c != "nombre" else 200, anchor="w")
        self.tree.pack(fill="both", expand=True, padx=6, pady=6)

#Botones de accion
        bar = ttk.Frame(self.root, padding=6)
        bar.pack(side="bottom", fill="x")
        ttk.Button(bar, text="Añadir disco", command=self.on_add).pack(side="left")
        ttk.Button(bar, text="Modificar disco", command=self.on_edit).pack(side="left", padx=6)
        ttk.Button(bar, text="Eliminar disco", command=self.on_delete).pack(side="left")
        ttk.Button(bar, text="Añadir stock", command=self.on_add_stock).pack(side="left", padx=6)

#Numero de version
        self.lbl_ver = ttk.Label(self.root, text="Versión 1.0 | " "Disenado por Cristian Pareja y Fabian Vega")
        self.lbl_ver.place(relx=1.0, rely=1.0, anchor="se")

        self.discos_cache = []
        self.cargar_todo()
        self.root.mainloop()

#Metodos utilitarios para el Treeview
#Borra los elementos de una fila para que de paso a las busquedas
    def reiniciar_tree(self):
        for it in self.tree.get_children():
            self.tree.delete(it)
#Rellena los elementos de una fila segun la busqueda
    def relleno_filas(self, rows):
        self.reiniciar_tree()
        for r in rows:
            self.tree.insert("", "end", values=(
                r["id_disco"], r["nombre_disco"],
                (f"${float(r['precio']):.2f}" if r["precio"] is not None else ""),
                r["artista"], r["fecha_lanzamiento"], r["peso_mb"], r.get("genero", ""), r["stock"]
            ))
#Carga todos los disco del repositorio en la lista vacia cache creada anteriormente
    def cargar_todo(self):
        self.discos_cache = self.repo.ordenar_todo()
        self.relleno_filas(self.discos_cache)

#Carga todos los disco del repositorio en la lista vacia cache creada anteriormente
    def en_busqueda(self):
        txt = self.var_busqueda.get().strip()
        if not txt:
            self.cargar_todo()
            return
        rows = self.repo.buscar(txt)
        self.discos_cache = rows
        self.relleno_filas(rows)
#LLama al metodo de ordenamiento quickshort segun parametros de campo (combobox) y desc (checkbox) en la clase Main
    def en_ordenamiento(self):
        campo = self.var_field.get()
        desc = self.var_desc.get()
        keymap = {
            "id": lambda r: r["id_disco"],
            "nombre": lambda r: (r["nombre_disco"] or "").lower(),
            "artista": lambda r: (r["artista"] or "").lower(),
            "genero": lambda r: (r.get("genero") or "").lower(),
            "stock": lambda r: int(r["stock"] or 0),
        }
        ordenados = quicksort(list(self.discos_cache), keymap[campo], reverse=desc)
        self.relleno_filas(ordenados)
#Metodo que se ejecuta con el boton anadir disco. 
    def on_add(self):
        #herencia (ventana secundaria de editor de disco)
        dialogo = EditorDisco(self.root)
        self.root.wait_window(dialogo)
        if dialogo.result:
            nombre, precio, artista, fecha, peso, genero, stock = dialogo.result
            try:
                new_id = self.repo.anadir(nombre, precio, artista, fecha, peso, genero, stock)
                self.logger.log("Agregar disco", f"ID {new_id} · {nombre} · {artista} · stock {stock}")
                messagebox.showinfo("Listo", "Disco agregado")
                self.cargar_todo()
            except Exception as e:
                messagebox.showerror("Error", str(e))
#Metodo que se ejecuta con el boton editar disco. 
    def on_edit(self):
        sel = self.tree.selection()
        if not sel:
            messagebox.showwarning("Atención", "Seleccione un disco")
            return
        item = self.tree.item(sel[0])
        id_disco = int(item["values"][0])
        row = self.repo.obtener_por_id_disco(id_disco)
        dialogo = EditorDisco(self.root, row)
        self.root.wait_window(dialogo)
        if dialogo.result:
            nombre, precio, artista, fecha, peso, genero, stock = dialogo.result
            try:
                self.repo.actualizar(id_disco, nombre, precio, artista, fecha, peso, genero, stock)
                self.logger.log("Modificar disco", f"ID {id_disco} → {nombre}/{artista}/stock {stock}")
                messagebox.showinfo("Listo", "Disco actualizado")
                self.cargar_todo()
            except Exception as e:
                messagebox.showerror("Error", str(e))

    def on_delete(self):
        sel = self.tree.selection()
        if not sel:
            messagebox.showwarning("Atención", "Seleccione un disco")
            return
        item = self.tree.item(sel[0])
        id_disco = int(item["values"][0])
        row = self.repo.obtener_por_id_disco(id_disco)
        if messagebox.askyesno("Confirmar", f"¿Eliminar '{row['nombre_disco']}' de {row['artista']}?"):
            try:
                self.repo.eliminar(id_disco)
                self.logger.log("Eliminar disco", f"ID {id_disco} · {row['nombre_disco']}")
                messagebox.showinfo("Listo", "Disco eliminado")
                self.cargar_todo()
            except Exception as e:
                messagebox.showerror("Error", str(e))

    def on_add_stock(self):
        sel = self.tree.selection()
        if not sel:
            messagebox.showwarning("Atención", "Seleccione un disco")
            return
        item = self.tree.item(sel[0])
        id_disco = int(item["values"][0])
        row = self.repo.obtener_por_id_disco(id_disco)
        cantidad = simpledialog.askinteger("Añadir Stock", f"¿Cuántas unidades añadir a '{row['nombre_disco']}'?", minvalue=1)
        if not cantidad:
            return
        try:
            nuevo = self.repo.anadir_stock(id_disco, cantidad, self.user["id"])
            self.logger.log("Añadir stock", f"ID {id_disco} +{cantidad} (nuevo stock={nuevo})")
            messagebox.showinfo("Listo", f"Stock actualizado: {nuevo}")
            self.cargar_todo()
        except Exception as e:
            messagebox.showerror("Error", str(e))

    def on_export_log(self):
        self.logger.exportar_log()

    def logout(self):
        self.root.destroy()
        LoginWindow()  # volver al login


# Capa de Administrador de Usuarios (solo Gerencia)

class UserAdmin(tk.Toplevel):
    def __init__(self, master, auth: GestorAutenticacion):
        super().__init__(master)
        self.title("Gestión de Usuarios")
        self.auth = auth
        self.resizable(False, False)

        ttk.Label(self, text="Nombre y Apellido").grid(row=0, column=0, sticky="e", padx=6, pady=4)
        ttk.Label(self, text="Correo").grid(row=1, column=0, sticky="e", padx=6, pady=4)
        ttk.Label(self, text="Perfil (1=Gerencia,2=Bodega,3=Vendedores)").grid(row=2, column=0, sticky="e", padx=6, pady=4)
        ttk.Label(self, text="Contraseña (opcional)").grid(row=3, column=0, sticky="e", padx=6, pady=4)

        self.e_nombre = ttk.Entry(self, width=30); self.e_nombre.grid(row=0, column=1, padx=6, pady=4)
        self.e_correo = ttk.Entry(self, width=30); self.e_correo.grid(row=1, column=1, padx=6, pady=4)
        self.e_perfil = ttk.Entry(self, width=10); self.e_perfil.grid(row=2, column=1, padx=6, pady=4, sticky="w")
        self.e_pass   = ttk.Entry(self, width=30, show="*"); self.e_pass.grid(row=3, column=1, padx=6, pady=4)

        ttk.Button(self, text="Agregar Usuario", command=self.add_user).grid(row=4, column=0, pady=8)
        ttk.Button(self, text="Eliminar Usuario", command=self.delete_user).grid(row=4, column=1, pady=8)

    def add_user(self):
        nombre = self.e_nombre.get().strip()
        correo = self.e_correo.get().strip()
        try:
            perfil = int(self.e_perfil.get().strip())
        except:
            messagebox.showwarning("Validación", "Perfil inválido")
            return
        pwd = self.e_pass.get().strip() or None
        if self.auth.anadir_usuario(nombre, correo, perfil, pwd):
            messagebox.showinfo("OK", "Usuario agregado")

    def delete_user(self):
        nombre = self.e_nombre.get().strip()
        if not nombre:
            messagebox.showwarning("Validación", "Indique el nombre de usuario a eliminar")
            return
        self.auth.eliminar_usuario(nombre)


# Capa de ventana de Login

class LoginWindow:
    def __init__(self):
        self.auth = GestorAutenticacion()

        self.win = tk.Tk()
        self.win.title("FloydMusic — Login")
        self.win.geometry("420x200")

        frm = ttk.Frame(self.win, padding=12)
        frm.pack(fill="both", expand=True)

        ttk.Label(frm, text="Usuario (Nombre y Apellido)").grid(row=0, column=0, sticky="e", pady=6)
        ttk.Label(frm, text="Contraseña (primer_nombre + 123)").grid(row=1, column=0, sticky="e", pady=6)

        self.e_user = ttk.Entry(frm, width=30); self.e_user.grid(row=0, column=1, padx=6)
        self.e_pass = ttk.Entry(frm, width=30, show="*"); self.e_pass.grid(row=1, column=1, padx=6)
        ttk.Button(frm, text="Ingresar", command=self.intentar_loguear).grid(row=2, column=0, columnspan=2, pady=12)
        self.win.mainloop()

    def intentar_loguear(self):
        u = self.e_user.get().strip()
        p = self.e_pass.get().strip()
        user = self.auth.autenticacion(u, p)
        if user:
            self.win.destroy()
            MainApp(user)
        else:
            messagebox.showerror("Login", "Usuario o contraseña incorrectos")

#Crea una instancia de UserAdmin, pasando root (ventana principal tkinter) y auth (tabla de usuarios y passwaords)
def abrir_admin_usuarios(root, auth):
    UserAdmin(root, auth)

# Vincular método al MainApp 
MainApp.abrir_admin_usuarios = lambda self: UserAdmin(self.root, self.auth)

# Ventana Inicial de login
if __name__ == "__main__":
    LoginWindow()
