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

-- Volcando estructura para tabla operaciones_dulce_tia.activos
CREATE TABLE IF NOT EXISTS `activos` (
  `id_activo` int NOT NULL AUTO_INCREMENT,
  `nombre` varchar(100) NOT NULL,
  `tipo` enum('empaque','utensilio','herramienta','costo_indirecto','servicio','transporte','mobiliario','otro') NOT NULL,
  `costo_unitario` decimal(10,2) NOT NULL DEFAULT '0.00',
  `stock_actual` decimal(10,2) DEFAULT '0.00',
  `unidad` varchar(30) DEFAULT NULL,
  `descripcion` text,
  `estado` enum('activo','inactivo') NOT NULL DEFAULT 'activo',
  `proveedor` varchar(100) DEFAULT NULL,
  `codigo_interno` varchar(50) DEFAULT NULL,
  `observaciones` text,
  `modalidad_costo` enum('por_unidad','mensual','por_hora','por_uso','porcentaje') NOT NULL DEFAULT 'por_unidad',
  `unidad_costo` varchar(30) DEFAULT NULL,
  `periodo` varchar(30) DEFAULT NULL,
  `vida_util_meses` int DEFAULT NULL,
  `valor_residual` decimal(10,2) DEFAULT '0.00',
  `fecha_registro` datetime DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id_activo`),
  KEY `idx_tipo` (`tipo`),
  KEY `idx_nombre` (`nombre`)
) ENGINE=MyISAM AUTO_INCREMENT=6 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

-- Volcando datos para la tabla operaciones_dulce_tia.activos: 5 rows
INSERT INTO `activos` (`id_activo`, `nombre`, `tipo`, `costo_unitario`, `stock_actual`, `unidad`, `descripcion`, `estado`, `proveedor`, `codigo_interno`, `observaciones`, `modalidad_costo`, `unidad_costo`, `periodo`, `vida_util_meses`, `valor_residual`, `fecha_registro`) VALUES
	(1, 'Licuadora', 'herramienta', 25.00, 2.00, 'unidad', '', 'activo', 'Chino', '1', '', 'por_unidad', '', '', 24, 10.00, '2026-07-18 22:56:06'),
	(2, 'Gas', 'servicio', 3.00, 0.00, 'unidad', '', 'activo', 'Vecino', '2', '', 'por_unidad', '', '', NULL, 0.00, '2026-07-18 22:59:39'),
	(3, 'Horno', 'herramienta', 400.00, 1.00, 'unidad', '', 'activo', 'Persona', '3', '', 'por_unidad', '', '', 96, 150.00, '2026-07-18 23:32:38'),
	(4, 'Batidora', 'herramienta', 30.00, 3.00, 'unidad', '', 'activo', 'Chinos', '3', '', 'por_unidad', '', '', 24, 5.00, '2026-07-18 23:33:22'),
	(5, 'Espatula', 'utensilio', 1.30, 3.00, 'unidad', '', 'activo', 'chinos', '09', '', 'por_unidad', '', '', 7, 0.00, '2026-07-23 10:29:57');

/*!40103 SET TIME_ZONE=IFNULL(@OLD_TIME_ZONE, 'system') */;
/*!40101 SET SQL_MODE=IFNULL(@OLD_SQL_MODE, '') */;
/*!40014 SET FOREIGN_KEY_CHECKS=IFNULL(@OLD_FOREIGN_KEY_CHECKS, 1) */;
/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40111 SET SQL_NOTES=IFNULL(@OLD_SQL_NOTES, 1) */;
