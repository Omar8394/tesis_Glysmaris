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

-- Volcando estructura para tabla operaciones_dulce_tia.receta_ingredientes
CREATE TABLE IF NOT EXISTS `receta_ingredientes` (
  `id_receta_ingrediente` int NOT NULL AUTO_INCREMENT,
  `id_receta` int NOT NULL,
  `id_ingrediente` int NOT NULL,
  `cantidad_necesaria` decimal(10,4) NOT NULL,
  `unidad` varchar(200) NOT NULL,
  PRIMARY KEY (`id_receta_ingrediente`),
  KEY `id_receta` (`id_receta`),
  KEY `id_ingrediente` (`id_ingrediente`)
) ENGINE=MyISAM AUTO_INCREMENT=14 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

-- Volcando datos para la tabla operaciones_dulce_tia.receta_ingredientes: 13 rows
INSERT INTO `receta_ingredientes` (`id_receta_ingrediente`, `id_receta`, `id_ingrediente`, `cantidad_necesaria`, `unidad`) VALUES
	(1, 1, 12, 200.0000, 'ml'),
	(2, 1, 11, 4.0000, 'unidad'),
	(3, 1, 8, 500.0000, 'g'),
	(4, 1, 15, 15.0000, 'ml'),
	(5, 1, 9, 250.0000, 'g'),
	(6, 1, 14, 10.0000, 'g'),
	(7, 1, 10, 250.0000, 'g'),
	(8, 2, 15, 5.0000, 'ml'),
	(9, 2, 11, 3.0000, 'unidad'),
	(10, 2, 9, 100.0000, 'g'),
	(11, 3, 15, 5.0000, 'ml'),
	(12, 3, 11, 3.0000, 'unidad'),
	(13, 3, 9, 100.0000, 'g');

/*!40103 SET TIME_ZONE=IFNULL(@OLD_TIME_ZONE, 'system') */;
/*!40101 SET SQL_MODE=IFNULL(@OLD_SQL_MODE, '') */;
/*!40014 SET FOREIGN_KEY_CHECKS=IFNULL(@OLD_FOREIGN_KEY_CHECKS, 1) */;
/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40111 SET SQL_NOTES=IFNULL(@OLD_SQL_NOTES, 1) */;
