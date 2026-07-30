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

-- Volcando estructura para tabla operaciones_dulce_tia.produccion_ingredientes_reservados
CREATE TABLE IF NOT EXISTS `produccion_ingredientes_reservados` (
  `id_reserva` int NOT NULL AUTO_INCREMENT,
  `id_orden` int NOT NULL,
  `id_detalle` int NOT NULL,
  `id_producto` int NOT NULL,
  `id_ingrediente` int NOT NULL,
  `id_lote` int DEFAULT NULL,
  `cantidad_reservada` decimal(10,2) NOT NULL,
  `cantidad_consumida` decimal(10,2) DEFAULT '0.00',
  `cantidad_devuelta` decimal(10,2) DEFAULT '0.00',
  `fecha_reserva` datetime DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id_reserva`),
  KEY `id_ingrediente` (`id_ingrediente`),
  KEY `id_lote` (`id_lote`),
  KEY `idx_orden` (`id_orden`),
  KEY `idx_detalle` (`id_detalle`),
  KEY `idx_producto` (`id_producto`)
) ENGINE=MyISAM AUTO_INCREMENT=11 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

-- Volcando datos para la tabla operaciones_dulce_tia.produccion_ingredientes_reservados: 10 rows
INSERT INTO `produccion_ingredientes_reservados` (`id_reserva`, `id_orden`, `id_detalle`, `id_producto`, `id_ingrediente`, `id_lote`, `cantidad_reservada`, `cantidad_consumida`, `cantidad_devuelta`, `fecha_reserva`) VALUES
	(1, 1, 1, 1, 12, 12, 0.33, 0.33, 0.00, '2026-07-30 11:39:57'),
	(2, 1, 1, 1, 11, 11, 6.56, 6.56, 0.00, '2026-07-30 11:39:57'),
	(3, 1, 1, 1, 8, 8, 0.82, 0.82, 0.00, '2026-07-30 11:39:57'),
	(4, 1, 1, 1, 15, 15, 24.59, 24.59, 0.00, '2026-07-30 11:39:57'),
	(5, 1, 1, 1, 9, 9, 0.41, 0.41, 0.00, '2026-07-30 11:39:57'),
	(6, 1, 1, 1, 14, 14, 16.39, 16.39, 0.00, '2026-07-30 11:39:57'),
	(7, 1, 1, 1, 10, 10, 409.84, 409.84, 0.00, '2026-07-30 11:39:57'),
	(8, 2, 2, 3, 15, 15, 0.42, 0.42, 0.00, '2026-07-30 18:12:29'),
	(9, 2, 2, 3, 11, 11, 0.25, 0.25, 0.00, '2026-07-30 18:12:29'),
	(10, 2, 2, 3, 9, 9, 0.01, 0.01, 0.00, '2026-07-30 18:12:29');

/*!40103 SET TIME_ZONE=IFNULL(@OLD_TIME_ZONE, 'system') */;
/*!40101 SET SQL_MODE=IFNULL(@OLD_SQL_MODE, '') */;
/*!40014 SET FOREIGN_KEY_CHECKS=IFNULL(@OLD_FOREIGN_KEY_CHECKS, 1) */;
/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40111 SET SQL_NOTES=IFNULL(@OLD_SQL_NOTES, 1) */;
