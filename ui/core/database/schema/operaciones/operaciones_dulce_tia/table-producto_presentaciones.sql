-- --------------------------------------------------------
-- Host:                         127.0.0.1
-- Versión del servidor:         9.1.0 - MySQL Community Server - GPL
-- SO del servidor:              Win64
-- HeidiSQL Versión:             12.18.0.7304
-- --------------------------------------------------------

/*!40101 SET @OLD_CHARACTER_SET_CLIENT=@@CHARACTER_SET_CLIENT */;
/*!40101 SET NAMES utf8 */;
/*!50503 SET NAMES utf8mb4 */;
/*!40103 SET @OLD_TIME_ZONE=@@TIME_ZONE */;
/*!40103 SET TIME_ZONE='+00:00' */;
/*!40014 SET @OLD_FOREIGN_KEY_CHECKS=@@FOREIGN_KEY_CHECKS, FOREIGN_KEY_CHECKS=0 */;
/*!40101 SET @OLD_SQL_MODE=@@SQL_MODE, SQL_MODE='NO_AUTO_VALUE_ON_ZERO' */;
/*!40111 SET @OLD_SQL_NOTES=@@SQL_NOTES, SQL_NOTES=0 */;

-- Volcando estructura para tabla operaciones_dulce_tia.producto_presentaciones
CREATE TABLE IF NOT EXISTS `producto_presentaciones` (
  `id_presentacion` int NOT NULL AUTO_INCREMENT,
  `id_producto` int NOT NULL,
  `nombre` varchar(100) NOT NULL,
  `precio` decimal(10,2) NOT NULL DEFAULT '0.00',
  `diametro_cm` decimal(6,2) DEFAULT NULL,
  `cantidad_trozos` int DEFAULT NULL,
  `diametro` decimal(10,2) DEFAULT NULL,
  `peso` decimal(10,2) DEFAULT NULL,
  `id_receta` int DEFAULT NULL,
  `costo` decimal(10,2) DEFAULT '0.00',
  `estado` enum('activo','inactivo') DEFAULT 'activo',
  PRIMARY KEY (`id_presentacion`),
  KEY `id_producto` (`id_producto`),
  KEY `id_receta` (`id_receta`)
) ENGINE=MyISAM AUTO_INCREMENT=2 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

-- Volcando datos para la tabla operaciones_dulce_tia.producto_presentaciones: 1 rows
INSERT INTO `producto_presentaciones` (`id_presentacion`, `id_producto`, `nombre`, `precio`, `diametro_cm`, `cantidad_trozos`, `diametro`, `peso`, `id_receta`, `costo`, `estado`) VALUES
	(1, 1, 'Trozo de torta', 5.12, NULL, NULL, NULL, NULL, NULL, 0.00, 'activo');

/*!40103 SET TIME_ZONE=IFNULL(@OLD_TIME_ZONE, 'system') */;
/*!40101 SET SQL_MODE=IFNULL(@OLD_SQL_MODE, '') */;
/*!40014 SET FOREIGN_KEY_CHECKS=IFNULL(@OLD_FOREIGN_KEY_CHECKS, 1) */;
/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40111 SET SQL_NOTES=IFNULL(@OLD_SQL_NOTES, 1) */;
