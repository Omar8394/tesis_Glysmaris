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

-- Volcando estructura para tabla operaciones_dulce_tia.produccion_mermas
CREATE TABLE IF NOT EXISTS `produccion_mermas` (
  `id_merma` int NOT NULL AUTO_INCREMENT,
  `id_orden` int NOT NULL,
  `id_detalle` int DEFAULT NULL,
  `id_producto` int DEFAULT NULL,
  `cantidad` decimal(10,2) NOT NULL,
  `tipo_merma` enum('recuperable','no_recuperable') NOT NULL,
  `motivo` enum('quemado','rotura','contaminacion','error_preparacion','decoracion','otro') NOT NULL,
  `descripcion` text,
  `costo_asociado` decimal(10,2) DEFAULT '0.00',
  `fecha_registro` datetime DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id_merma`),
  KEY `id_producto` (`id_producto`),
  KEY `idx_orden` (`id_orden`),
  KEY `idx_detalle` (`id_detalle`)
) ENGINE=MyISAM AUTO_INCREMENT=2 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

-- Volcando datos para la tabla operaciones_dulce_tia.produccion_mermas: 1 rows
INSERT INTO `produccion_mermas` (`id_merma`, `id_orden`, `id_detalle`, `id_producto`, `cantidad`, `tipo_merma`, `motivo`, `descripcion`, `costo_asociado`, `fecha_registro`) VALUES
	(1, 2, 2, 3, 3.00, 'recuperable', 'otro', '', 0.00, '2026-07-30 18:12:52');

/*!40103 SET TIME_ZONE=IFNULL(@OLD_TIME_ZONE, 'system') */;
/*!40101 SET SQL_MODE=IFNULL(@OLD_SQL_MODE, '') */;
/*!40014 SET FOREIGN_KEY_CHECKS=IFNULL(@OLD_FOREIGN_KEY_CHECKS, 1) */;
/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40111 SET SQL_NOTES=IFNULL(@OLD_SQL_NOTES, 1) */;
