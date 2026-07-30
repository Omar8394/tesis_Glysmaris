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

-- Volcando estructura para tabla operaciones_dulce_tia.perdidas_inventario
CREATE TABLE IF NOT EXISTS `perdidas_inventario` (
  `id_perdida` int NOT NULL AUTO_INCREMENT,
  `id_lote` int DEFAULT NULL,
  `nombre_ingrediente` varchar(100) DEFAULT NULL,
  `unidad_medida` varchar(30) DEFAULT NULL,
  `cantidad` decimal(10,2) NOT NULL,
  `motivo` enum('error_registro','perdida_material','caducidad','daño','otro') NOT NULL,
  `descripcion` text,
  `costo_perdida` decimal(10,2) DEFAULT NULL,
  `fecha` datetime DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id_perdida`),
  KEY `id_lote` (`id_lote`)
) ENGINE=MyISAM AUTO_INCREMENT=9 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

-- Volcando datos para la tabla operaciones_dulce_tia.perdidas_inventario: 8 rows
INSERT INTO `perdidas_inventario` (`id_perdida`, `id_lote`, `nombre_ingrediente`, `unidad_medida`, `cantidad`, `motivo`, `descripcion`, `costo_perdida`, `fecha`) VALUES
	(1, 4, 'Huevos', 'unidad', 11.72, 'error_registro', 'Error de inventario', 52.74, '2026-07-30 11:26:00'),
	(2, 5, 'Leche de Vaca', 'L', 1.84, 'error_registro', 'Error de inventario', 2.76, '2026-07-30 11:26:07'),
	(3, 1, 'Azucar Blanca', 'kg', 0.80, 'error_registro', 'Error de inventario', 0.96, '2026-07-30 11:26:13'),
	(4, 2, 'Harina de Trigo', 'kg', 1.59, 'error_registro', 'Error de inventario', 2.07, '2026-07-30 11:26:21'),
	(5, 3, 'Mantequilla', 'g', 295.08, 'error_registro', 'Error de inventario', 708.19, '2026-07-30 11:26:29'),
	(6, 7, 'Polvo para hornear', 'g', 191.80, 'error_registro', 'Error de inventario', 287.70, '2026-07-30 11:26:35'),
	(7, 6, 'Escencia de Vainilla', 'ml', 87.70, 'error_registro', 'Error de inventario', 87.70, '2026-07-30 11:26:41'),
	(8, 13, 'Escencia de Vainilla', 'ml', 100.00, 'error_registro', 'Error de inventario', 100.00, '2026-07-30 11:34:28');

/*!40103 SET TIME_ZONE=IFNULL(@OLD_TIME_ZONE, 'system') */;
/*!40101 SET SQL_MODE=IFNULL(@OLD_SQL_MODE, '') */;
/*!40014 SET FOREIGN_KEY_CHECKS=IFNULL(@OLD_FOREIGN_KEY_CHECKS, 1) */;
/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40111 SET SQL_NOTES=IFNULL(@OLD_SQL_NOTES, 1) */;
