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

-- Volcando estructura para tabla operaciones_dulce_tia.produccion_detalle
CREATE TABLE IF NOT EXISTS `produccion_detalle` (
  `id_detalle` int NOT NULL AUTO_INCREMENT,
  `id_orden` int NOT NULL,
  `id_producto` int NOT NULL,
  `id_presentacion` int DEFAULT NULL,
  `cantidad_planificada` int NOT NULL DEFAULT '1',
  `cantidad_obtenida` int DEFAULT '0',
  `peso_objetivo` decimal(10,2) DEFAULT NULL,
  `unidad_objetivo` varchar(20) DEFAULT NULL,
  `precio_final` decimal(10,2) DEFAULT '0.00',
  `modificaciones` text,
  `costo_calculado` decimal(10,2) DEFAULT '0.00',
  `rendimiento_porcentaje` decimal(5,2) DEFAULT '0.00',
  `disponible_venta` tinyint(1) DEFAULT '1',
  `cantidad_vendida` int NOT NULL DEFAULT '0',
  PRIMARY KEY (`id_detalle`),
  KEY `id_presentacion` (`id_presentacion`),
  KEY `idx_orden` (`id_orden`),
  KEY `idx_producto` (`id_producto`)
) ENGINE=MyISAM AUTO_INCREMENT=3 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

-- Volcando datos para la tabla operaciones_dulce_tia.produccion_detalle: 2 rows
INSERT INTO `produccion_detalle` (`id_detalle`, `id_orden`, `id_producto`, `id_presentacion`, `cantidad_planificada`, `cantidad_obtenida`, `peso_objetivo`, `unidad_objetivo`, `precio_final`, `modificaciones`, `costo_calculado`, `rendimiento_porcentaje`, `disponible_venta`, `cantidad_vendida`) VALUES
	(1, 1, 1, NULL, 2, 2, NULL, NULL, 0.00, '', 0.00, 100.00, 1, 0),
	(2, 2, 3, NULL, 1, 0, NULL, NULL, 0.00, '', 0.00, 0.00, 1, 0);

/*!40103 SET TIME_ZONE=IFNULL(@OLD_TIME_ZONE, 'system') */;
/*!40101 SET SQL_MODE=IFNULL(@OLD_SQL_MODE, '') */;
/*!40014 SET FOREIGN_KEY_CHECKS=IFNULL(@OLD_FOREIGN_KEY_CHECKS, 1) */;
/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40111 SET SQL_NOTES=IFNULL(@OLD_SQL_NOTES, 1) */;
