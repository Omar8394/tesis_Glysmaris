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

-- Volcando estructura para tabla operaciones_dulce_tia.produccion_activos_reservados
CREATE TABLE IF NOT EXISTS `produccion_activos_reservados` (
  `id_reserva_activo` int NOT NULL AUTO_INCREMENT,
  `id_orden` int NOT NULL,
  `id_detalle` int NOT NULL,
  `id_producto` int NOT NULL,
  `id_activo` int NOT NULL,
  `cantidad_reservada` decimal(10,2) NOT NULL,
  `cantidad_consumida` decimal(10,2) DEFAULT '0.00',
  `fecha_reserva` datetime DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id_reserva_activo`),
  KEY `id_producto` (`id_producto`),
  KEY `id_activo` (`id_activo`),
  KEY `idx_orden` (`id_orden`),
  KEY `idx_detalle` (`id_detalle`)
) ENGINE=MyISAM DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

-- Volcando datos para la tabla operaciones_dulce_tia.produccion_activos_reservados: 0 rows

/*!40103 SET TIME_ZONE=IFNULL(@OLD_TIME_ZONE, 'system') */;
/*!40101 SET SQL_MODE=IFNULL(@OLD_SQL_MODE, '') */;
/*!40014 SET FOREIGN_KEY_CHECKS=IFNULL(@OLD_FOREIGN_KEY_CHECKS, 1) */;
/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40111 SET SQL_NOTES=IFNULL(@OLD_SQL_NOTES, 1) */;
