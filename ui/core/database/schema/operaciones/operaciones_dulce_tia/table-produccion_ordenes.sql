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

-- Volcando estructura para tabla operaciones_dulce_tia.produccion_ordenes
CREATE TABLE IF NOT EXISTS `produccion_ordenes` (
  `id_orden` int NOT NULL AUTO_INCREMENT,
  `numero_orden` varchar(20) NOT NULL,
  `fecha_creacion` datetime DEFAULT CURRENT_TIMESTAMP,
  `fecha_planificada` date NOT NULL,
  `hora_estimada` time DEFAULT NULL,
  `prioridad` enum('baja','media','alta','urgente') DEFAULT 'media',
  `responsable` varchar(100) DEFAULT NULL,
  `estado` enum('pendiente','en_proceso','finalizada','cancelada') DEFAULT 'pendiente',
  `avance_manual` int NOT NULL DEFAULT '0',
  `notas` text,
  `costo_estimado` decimal(10,2) DEFAULT '0.00',
  `costo_real` decimal(10,2) DEFAULT '0.00',
  `tiempo_estimado_minutos` int DEFAULT '0',
  `tiempo_real_minutos` int DEFAULT '0',
  `fecha_inicio` datetime DEFAULT NULL,
  `fecha_fin` datetime DEFAULT NULL,
  `creado_por` varchar(100) DEFAULT NULL,
  PRIMARY KEY (`id_orden`),
  UNIQUE KEY `numero_orden` (`numero_orden`),
  KEY `idx_estado` (`estado`),
  KEY `idx_fecha` (`fecha_planificada`),
  KEY `idx_prioridad` (`prioridad`),
  KEY `idx_numero` (`numero_orden`)
) ENGINE=MyISAM AUTO_INCREMENT=3 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

-- Volcando datos para la tabla operaciones_dulce_tia.produccion_ordenes: 2 rows
INSERT INTO `produccion_ordenes` (`id_orden`, `numero_orden`, `fecha_creacion`, `fecha_planificada`, `hora_estimada`, `prioridad`, `responsable`, `estado`, `avance_manual`, `notas`, `costo_estimado`, `costo_real`, `tiempo_estimado_minutos`, `tiempo_real_minutos`, `fecha_inicio`, `fecha_fin`, `creado_por`) VALUES
	(1, 'ORD-2026-00001', '2026-07-30 11:39:53', '2026-07-30', '02:00:00', 'baja', 'QW', 'finalizada', 0, '', 10.24, 0.00, 0, 0, '2026-07-30 11:39:57', '2026-07-30 11:40:29', 'admin'),
	(2, 'ORD-2026-00002', '2026-07-30 18:12:26', '2026-07-30', '12:00:00', 'baja', 'er', 'finalizada', 0, '', 0.90, 0.00, 0, 0, '2026-07-30 18:12:29', '2026-07-30 18:12:52', 'admin');

/*!40103 SET TIME_ZONE=IFNULL(@OLD_TIME_ZONE, 'system') */;
/*!40101 SET SQL_MODE=IFNULL(@OLD_SQL_MODE, '') */;
/*!40014 SET FOREIGN_KEY_CHECKS=IFNULL(@OLD_FOREIGN_KEY_CHECKS, 1) */;
/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40111 SET SQL_NOTES=IFNULL(@OLD_SQL_NOTES, 1) */;
