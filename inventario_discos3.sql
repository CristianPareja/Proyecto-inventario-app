--1. Tabla perfil (perfiles de los usuarios)
CREATE TABLE perfil ( 
id_perfil serial NOT NULL, 
nombre_perfil varchar(50), 
PRIMARY KEY (id_perfil) 
);

--2. Tabla usuario (informacion de los usuarios de la app)
CREATE TABLE usuario (
id_usuario serial NOT NULL,
cedula int UNIQUE, 
nombre_usuario varchar (50) NOT NULL UNIQUE,
edad int, 
genero varchar(50), 
correo varchar(50), 
id_perfil1 int, 
PRIMARY KEY (id_usuario), 
CONSTRAINT fk_perfil_usuario FOREIGN KEY (id_perfil1) REFERENCES perfil (id_perfil) 
);

--3. Tabla auth (autenticacion) 
CREATE TABLE auth ( 
id_usuario SERIAL PRIMARY KEY, 
password_hash VARCHAR(256) NOT NULL, 
FOREIGN KEY (id_usuario) REFERENCES usuario(id_usuario) ON DELETE CASCADE
);

--4 Tabla disco_musica 
CREATE TABLE disco_musica ( 
id_disco serial NOT NULL, 
nombre_disco varchar(100) NOT NULL, 
precio decimal, 
artista varchar(100), 
fecha_lanzamiento date, 
peso_MB decimal, 
genero varchar(50), 
stock int DEFAULT 0,
PRIMARY KEY (id_disco) 
);

--5. Tabla movimiento_inventario entradas/salidas de stock
CREATE TABLE movimiento_inventario ( 
id_movimiento serial PRIMARY KEY, 
id_usuario int NOT NULL, 
id_disco int NOT NULL, 
tipo varchar(20) CHECK (tipo IN ('entrada', 'salida')), 
cantidad int NOT NULL CHECK (cantidad > 0), 
fecha timestamp DEFAULT CURRENT_TIMESTAMP, FOREIGN KEY (id_usuario) REFERENCES usuario(id_usuario), FOREIGN KEY (id_disco) REFERENCES disco_musica(id_disco) 
);

--6 Insertamos discos
INSERT INTO disco_musica (nombre_disco, precio, artista, fecha_lanzamiento, peso_MB, genero, stock) 
VALUES('Thriller', 15.99, 'Michael Jackson', '1982-11-30', 120, 'Pop', 120),
    ('Back in Black', 14.50, 'AC/DC', '1980-07-25', 110, 'Rock', 80),
    ('The Dark Side of the Moon', 13.99, 'Pink Floyd', '1973-03-01', 105, 'Rock', 60),
    ('Abbey Road', 16.99, 'The Beatles', '1969-09-26', 115, 'Rock', 150),
    ('Hotel California', 14.99, 'Eagles', '1976-12-08', 118, 'Rock', 95),
    ('21', 13.50, 'Adele', '2011-01-24', 102, 'Pop', 200),
    ('Nevermind', 15.20, 'Nirvana', '1991-09-24', 110, 'Grunge', 123),
    ('Born in the U.S.A.', 12.80, 'Bruce Springsteen', '1984-06-04', 108, 'Rock', 67),
    ('Rumours', 13.75, 'Fleetwood Mac', '1977-02-04', 107, 'Rock', 88),
    ('Led Zeppelin IV', 15.40, 'Led Zeppelin', '1971-11-08', 111, 'Rock', 142),
    ('Like a Virgin', 12.90, 'Madonna', '1984-11-12', 100, 'Pop', 59),
    ('Bad', 14.10, 'Michael Jackson', '1987-08-31', 119, 'Pop', 175),
    ('Purple Rain', 15.60, 'Prince', '1984-06-25', 113, 'Pop', 131),
    ('1989', 13.80, 'Taylor Swift', '2014-10-27', 104, 'Pop', 95),
    ('Appetite for Destruction', 16.10, 'Guns N’ Roses', '1987-07-21', 117, 'Rock', 70),
    ('OK Computer', 15.70, 'Radiohead', '1997-05-21', 112, 'Alternative', 121),
    ('Parachutes', 12.60, 'Coldplay', '2000-07-10', 106, 'Alternative', 89),
    ('A Night at the Opera', 14.80, 'Queen', '1975-11-21', 114, 'Rock', 147),
    ('Slippery When Wet', 13.40, 'Bon Jovi', '1986-08-18', 109, 'Rock', 160),
    ('Goodbye Yellow Brick Road', 15.20, 'Elton John', '1973-10-05', 111, 'Pop', 74),
    ('The Wall', 16.50, 'Pink Floyd', '1979-11-30', 118, 'Rock', 186),
    ('Californication', 14.70, 'Red Hot Chili Peppers', '1999-06-08', 109, 'Funk Rock', 93),
    ('American Idiot', 13.90, 'Green Day', '2004-09-21', 110, 'Punk Rock', 125),
    ('Hybrid Theory', 14.20, 'Linkin Park', '2000-10-24', 112, 'Nu Metal', 172),
    ('Hounds of Love', 12.80, 'Kate Bush', '1985-09-16', 108, 'Art Pop', 69),
    ('Random Access Memories', 15.90, 'Daft Punk', '2013-05-17', 120, 'Electronic', 180),
    ('Bangerz', 13.30, 'Miley Cyrus', '2013-10-04', 103, 'Pop', 140),
    ('Hot Fuss', 14.60, 'The Killers', '2004-06-07', 107, 'Alternative', 84),
    ('X&Y', 14.00, 'Coldplay', '2005-06-06', 111, 'Alternative', 191),
    ('Future Nostalgia', 13.50, 'Dua Lipa', '2020-03-27', 102, 'Pop', 133),
    ('25', 14.40, 'Adele', '2015-11-20', 106, 'Pop', 178),
    ('Fearless', 13.20, 'Taylor Swift', '2008-11-11', 104, 'Pop', 152),
    ('Red', 15.00, 'Taylor Swift', '2012-10-22', 115, 'Pop', 143),
    ('Divide', 14.50, 'Ed Sheeran', '2017-03-03', 110, 'Pop', 91),
    ('Multiply', 13.70, 'Ed Sheeran', '2014-06-20', 109, 'Pop', 118),
    ('Un Verano Sin Ti', 15.80, 'Bad Bunny', '2022-05-06', 119, 'Reggaeton', 200),
    ('YHLQMDLG', 14.20, 'Bad Bunny', '2020-02-29', 117, 'Reggaeton', 136),
    ('El Madrileño', 13.90, 'C. Tangana', '2021-02-26', 114, 'Pop Urbano', 87),
    ('Colores', 12.70, 'J Balvin', '2020-03-19', 110, 'Reggaeton', 168),
    ('Discovery', 15.50, 'Daft Punk', '2001-03-12', 112, 'Electronic', 105),
    ('Homework', 14.10, 'Daft Punk', '1997-01-20', 109, 'Electronic', 157),
    ('Doo-Wops & Hooligans', 13.40, 'Bruno Mars', '2010-10-04', 106, 'Pop', 176),
    ('24K Magic', 14.80, 'Bruno Mars', '2016-11-18', 113, 'Pop', 167),
    ('Confessions', 13.60, 'Usher', '2004-03-23', 111, 'R&B', 148),
    ('The Eminem Show', 14.20, 'Eminem', '2002-05-26', 116, 'Rap', 172),
    ('Recovery', 14.90, 'Eminem', '2010-06-18', 115, 'Rap', 154),
    ('Scorpion', 15.10, 'Drake', '2018-06-29', 118, 'Rap', 132),
    ('Views', 14.30, 'Drake', '2016-04-29', 114, 'Rap', 98),
    ('DAMN.', 15.60, 'Kendrick Lamar', '2017-04-14', 116, 'Rap', 141),
    ('To Pimp a Butterfly', 16.00, 'Kendrick Lamar', '2015-03-15', 118, 'Rap', 163),
    ('Astroworld', 15.70, 'Travis Scott', '2018-08-03', 117, 'Rap', 126),
    ('Culture', 14.80, 'Migos', '2017-01-27', 112, 'Rap', 174);

--7 Insertamos perfiles
INSERT INTO perfil (id_perfil, nombre_perfil) 
VALUES (1, 'Gerencia'), (2, 'Bodega'), (3, 'Vendedores');