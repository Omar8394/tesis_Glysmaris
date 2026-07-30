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

-- Volcando estructura para tabla operaciones_dulce_tia.recetas
CREATE TABLE IF NOT EXISTS `recetas` (
  `id_receta` int NOT NULL AUTO_INCREMENT,
  `nombre_receta` varchar(100) NOT NULL,
  `tipo_receta` varchar(50) NOT NULL,
  `descripcion` text,
  `costo_ingredientes` decimal(10,2) NOT NULL DEFAULT '0.00',
  `rendimiento_cantidad` decimal(10,2) NOT NULL DEFAULT '1.00',
  `rendimiento_unidad` varchar(30) NOT NULL DEFAULT 'unidad',
  `fecha_creacion` datetime DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id_receta`)
) ENGINE=MyISAM AUTO_INCREMENT=4 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

-- Volcando datos para la tabla operaciones_dulce_tia.recetas: 3 rows
INSERT INTO `recetas` (`id_receta`, `nombre_receta`, `tipo_receta`, `descripcion`, `costo_ingredientes`, `rendimiento_cantidad`, `rendimiento_unidad`, `fecha_creacion`) VALUES
	(1, 'Bizcocho de Vainilla', 'Base', '', 3.35, 1.22, 'kg', '2026-07-30 11:37:57'),
	(2, 'Merengue', 'Cobertura', '', 0.62, 200.00, 'g', '2026-07-30 11:42:18'),
	(3, 'Suspiros', 'Receta clásica', '', 0.62, 12.00, 'unidad', '2026-07-30 18:10:51');

/*!40103 SET TIME_ZONE=IFNULL(@OLD_TIME_ZONE, 'system') */;
/*!40101 SET SQL_MODE=IFNULL(@OLD_SQL_MODE, '') */;
/*!40014 SET FOREIGN_KEY_CHECKS=IFNULL(@OLD_FOREIGN_KEY_CHECKS, 1) */;
/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40111 SET SQL_NOTES=IFNULL(@OLD_SQL_NOTES, 1) */;
