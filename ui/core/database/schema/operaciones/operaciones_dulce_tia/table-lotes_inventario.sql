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

-- Volcando estructura para tabla operaciones_dulce_tia.lotes_inventario
CREATE TABLE IF NOT EXISTS `lotes_inventario` (
  `id_lote` int NOT NULL AUTO_INCREMENT,
  `id_ingrediente` int NOT NULL,
  `stock_inicial` decimal(10,2) NOT NULL DEFAULT '0.00',
  `stock_actual` decimal(10,2) NOT NULL DEFAULT '0.00',
  `costo_unitario` decimal(10,4) NOT NULL DEFAULT '0.0000',
  `fecha_ingreso` date NOT NULL,
  `fecha_caducidad` date NOT NULL,
  PRIMARY KEY (`id_lote`),
  KEY `id_ingrediente` (`id_ingrediente`)
) ENGINE=MyISAM AUTO_INCREMENT=16 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

-- Volcando datos para la tabla operaciones_dulce_tia.lotes_inventario: 7 rows
INSERT INTO `lotes_inventario` (`id_lote`, `id_ingrediente`, `stock_inicial`, `stock_actual`, `costo_unitario`, `fecha_ingreso`, `fecha_caducidad`) VALUES
	(8, 8, 2.00, 1.18, 1.3000, '2026-07-30', '2026-12-21'),
	(9, 9, 2.00, 1.58, 1.2000, '2026-07-30', '2027-02-26'),
	(10, 10, 1000.00, 590.16, 2.4000, '2026-07-30', '2027-05-02'),
	(11, 11, 30.00, 23.19, 4.5000, '2026-07-30', '2026-08-19'),
	(12, 12, 2.00, 1.67, 1.5000, '2026-07-30', '2026-08-12'),
	(14, 14, 100.00, 83.61, 1.5000, '2026-07-30', '2027-04-01'),
	(15, 15, 100.00, 74.99, 1.0000, '2026-07-30', '2027-01-21');

/*!40103 SET TIME_ZONE=IFNULL(@OLD_TIME_ZONE, 'system') */;
/*!40101 SET SQL_MODE=IFNULL(@OLD_SQL_MODE, '') */;
/*!40014 SET FOREIGN_KEY_CHECKS=IFNULL(@OLD_FOREIGN_KEY_CHECKS, 1) */;
/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40111 SET SQL_NOTES=IFNULL(@OLD_SQL_NOTES, 1) */;
