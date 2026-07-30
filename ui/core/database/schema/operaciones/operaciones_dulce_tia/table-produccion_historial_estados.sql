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

-- Volcando estructura para tabla operaciones_dulce_tia.produccion_historial_estados
CREATE TABLE IF NOT EXISTS `produccion_historial_estados` (
  `id_historial` int NOT NULL AUTO_INCREMENT,
  `id_orden` int NOT NULL,
  `estado_anterior` enum('pendiente','en_proceso','finalizada','cancelada') NOT NULL,
  `estado_nuevo` enum('pendiente','en_proceso','finalizada','cancelada') NOT NULL,
  `fecha_cambio` datetime DEFAULT CURRENT_TIMESTAMP,
  `usuario` varchar(100) DEFAULT NULL,
  `observaciones` text,
  PRIMARY KEY (`id_historial`),
  KEY `idx_orden` (`id_orden`)
) ENGINE=MyISAM AUTO_INCREMENT=5 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

-- Volcando datos para la tabla operaciones_dulce_tia.produccion_historial_estados: 4 rows
INSERT INTO `produccion_historial_estados` (`id_historial`, `id_orden`, `estado_anterior`, `estado_nuevo`, `fecha_cambio`, `usuario`, `observaciones`) VALUES
	(1, 1, 'pendiente', 'en_proceso', '2026-07-30 11:39:57', NULL, NULL),
	(2, 1, 'en_proceso', 'finalizada', '2026-07-30 11:40:28', NULL, NULL),
	(3, 2, 'pendiente', 'en_proceso', '2026-07-30 18:12:29', NULL, NULL),
	(4, 2, 'en_proceso', 'finalizada', '2026-07-30 18:12:52', NULL, NULL);

/*!40103 SET TIME_ZONE=IFNULL(@OLD_TIME_ZONE, 'system') */;
/*!40101 SET SQL_MODE=IFNULL(@OLD_SQL_MODE, '') */;
/*!40014 SET FOREIGN_KEY_CHECKS=IFNULL(@OLD_FOREIGN_KEY_CHECKS, 1) */;
/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40111 SET SQL_NOTES=IFNULL(@OLD_SQL_NOTES, 1) */;
