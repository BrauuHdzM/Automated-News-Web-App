-- Creación de la tabla Usuario
CREATE TABLE Usuario (
    idUsuario INT NOT NULL PRIMARY KEY AUTO_INCREMENT,
    nombre CHAR(50) NOT NULL,
    usuario CHAR(20) NOT NULL,
    correo CHAR(30) NOT NULL,
    contraseña VARCHAR(255) NOT NULL
);

-- Creación de la tabla ArticuloNoticia
CREATE TABLE ArticuloNoticia (
    idArticulo INT NOT NULL PRIMARY KEY AUTO_INCREMENT,
    titulo CHAR(200) NOT NULL,
    contenido TEXT(500) NOT NULL,
    fecha DATE NOT NULL
);

-- Creación de la tabla CalificacionNoticia
CREATE TABLE CalificacionNoticia (
    idCalificacion INT NOT NULL PRIMARY KEY AUTO_INCREMENT,
    puntuacion INT,
    idUsuario INT NOT NULL,
    idArticulo INT NOT NULL,
    FOREIGN KEY (idUsuario) REFERENCES Usuario(idUsuario),
    FOREIGN KEY (idArticulo) REFERENCES ArticuloNoticia(idArticulo)
);

