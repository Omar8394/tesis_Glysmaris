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

-- Volcando estructura para tabla operaciones_dulce_tia.ingredientes
CREATE TABLE IF NOT EXISTS `ingredientes` (
  `id_ingrediente` int NOT NULL AUTO_INCREMENT,
  `nombre_ingrediente` varchar(100) NOT NULL,
  `unidad_medida` varchar(30) NOT NULL,
  `categoria` varchar(50) DEFAULT NULL,
  `perecedero` tinyint(1) DEFAULT '0',
  `refrigerado` tinyint(1) DEFAULT '0',
  `descripcion` text,
  `contenido_unidad` decimal(10,4) NOT NULL DEFAULT '1.0000',
  PRIMARY KEY (`id_ingrediente`),
  UNIQUE KEY `nombre_ingrediente` (`nombre_ingrediente`)
) ENGINE=MyISAM AUTO_INCREMENT=16 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

-- Volcando datos para la tabla operaciones_dulce_tia.ingredientes: 7 rows
INSERT INTO `ingredientes` (`id_ingrediente`, `nombre_ingrediente`, `unidad_medida`, `categoria`, `perecedero`, `refrigerado`, `descripcion`, `contenido_unidad`) VALUES
	(8, 'Harina de Trigo', 'kg', 'Elaboración', 0, 0, '', 1.0000),
	(9, 'Azucar Blanca', 'kg', 'Elaboración', 0, 0, '', 1.0000),
	(10, 'Mantequilla', 'g', 'Elaboración', 0, 0, '', 500.0000),
	(11, 'Huevos', 'unidad', 'Lácteos', 1, 1, '', 30.0000),
	(12, 'Leche de Vaca', 'L', 'Lácteos', 1, 1, '', 1.0000),
	(14, 'Polvo para hornear', 'g', 'Elaboración', 0, 0, '', 100.0000),
	(15, 'Escencia de Vainilla', 'ml', 'Esencias', 0, 0, '', 100.0000);

/*!40103 SET TIME_ZONE=IFNULL(@OLD_TIME_ZONE, 'system') */;
/*!40101 SET SQL_MODE=IFNULL(@OLD_SQL_MODE, '') */;
/*!40014 SET FOREIGN_KEY_CHECKS=IFNULL(@OLD_FOREIGN_KEY_CHECKS, 1) */;
/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40111 SET SQL_NOTES=IFNULL(@OLD_SQL_NOTES, 1) */;
