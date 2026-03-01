SET @OLD_UNIQUE_CHECKS=@@UNIQUE_CHECKS, UNIQUE_CHECKS=0;
SET @OLD_FOREIGN_KEY_CHECKS=@@FOREIGN_KEY_CHECKS, FOREIGN_KEY_CHECKS=0;

CREATE SCHEMA IF NOT EXISTS `tt` DEFAULT CHARACTER SET utf8mb4;
USE `tt`;

CREATE TABLE IF NOT EXISTS `tt`.`Usuario` (
  `idUsuario` INT NOT NULL AUTO_INCREMENT,
  `nombre` VARCHAR(255) NOT NULL,
  `usuario` VARCHAR(255) NOT NULL,
  `correo` VARCHAR(255) NOT NULL,
  `contraseña` VARCHAR(255) NOT NULL,
  `codigoVerificacion` CHAR(10) NOT NULL,
  `verificado` INT NULL DEFAULT 0,
  `esAdmin` INT NOT NULL DEFAULT 0,
  PRIMARY KEY (`idUsuario`)
) ENGINE = InnoDB AUTO_INCREMENT = 13;

CREATE TABLE IF NOT EXISTS `tt`.`ArticuloNoticia` (
  `idArticulo` INT NOT NULL AUTO_INCREMENT,
  `titulo` VARCHAR(255) NOT NULL,
  `contenido` TEXT NOT NULL,
  `fecha` VARCHAR(255) NOT NULL,
  `idUsuario` INT NOT NULL,
  `modeloLenguaje` VARCHAR(255) NOT NULL,
  PRIMARY KEY (`idArticulo`),
  INDEX `fk_usuario_articulo` (`idUsuario` ASC),
  CONSTRAINT `fk_usuario_articulo`
    FOREIGN KEY (`idUsuario`)
    REFERENCES `tt`.`Usuario` (`idUsuario`)
    ON DELETE CASCADE
    ON UPDATE CASCADE
) ENGINE = InnoDB AUTO_INCREMENT = 72;

CREATE TABLE IF NOT EXISTS `tt`.`CalificacionNoticia` (
  `idCalificacion` INT NOT NULL AUTO_INCREMENT,
  `calificacionTitulo` INT NULL DEFAULT 0,
  `calificacionContenido` INT NULL DEFAULT 0,
  `calificacionRedaccion` INT NULL DEFAULT 0,
  `idUsuario` INT NOT NULL,
  `idArticulo` INT NOT NULL,
  PRIMARY KEY (`idCalificacion`),
  CONSTRAINT `calificacionnoticia_ibfk_1`
    FOREIGN KEY (`idUsuario`)
    REFERENCES `tt`.`Usuario` (`idUsuario`)
    ON DELETE CASCADE,
  CONSTRAINT `calificacionnoticia_ibfk_2`
    FOREIGN KEY (`idArticulo`)
    REFERENCES `tt`.`ArticuloNoticia` (`idArticulo`)
    ON DELETE CASCADE
) ENGINE = InnoDB AUTO_INCREMENT = 9;

SET FOREIGN_KEY_CHECKS=@OLD_FOREIGN_KEY_CHECKS;
SET UNIQUE_CHECKS=@OLD_UNIQUE_CHECKS;