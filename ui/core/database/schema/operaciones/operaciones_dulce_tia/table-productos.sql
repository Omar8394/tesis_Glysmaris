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

-- Volcando estructura para tabla operaciones_dulce_tia.productos
CREATE TABLE IF NOT EXISTS `productos` (
  `id_producto` int NOT NULL AUTO_INCREMENT,
  `nombre_producto` varchar(150) NOT NULL,
  `tipo_producto` varchar(50) DEFAULT NULL,
  `categoria` varchar(50) DEFAULT NULL,
  `precio_venta` decimal(10,2) DEFAULT '0.00',
  `peso` decimal(10,2) DEFAULT '1.00',
  `unidad_peso` varchar(20) DEFAULT 'kg',
  `receta_id` int DEFAULT NULL,
  `producto_padre_id` int DEFAULT NULL,
  `descripcion_producto` text,
  `fecha_creacion` datetime DEFAULT CURRENT_TIMESTAMP,
  `activo` tinyint(1) DEFAULT '1',
  `sabor_producto` varchar(100) DEFAULT NULL,
  `relleno_producto` varchar(100) DEFAULT NULL,
  `cobertura_producto` varchar(100) DEFAULT NULL,
  `costo_receta` decimal(10,2) DEFAULT '0.00',
  `tiempo_preparacion_minutos` decimal(10,2) DEFAULT '0.00',
  `mano_obra` decimal(10,2) DEFAULT '0.00',
  `empaques` decimal(10,2) DEFAULT '0.00',
  `costos_indirectos` decimal(10,2) DEFAULT '0.00',
  `margen_porcentaje` decimal(5,2) DEFAULT '40.00',
  `precio_sugerido` decimal(10,2) NOT NULL DEFAULT '0.00',
  `costo_total` decimal(10,2) DEFAULT '0.00',
  `precio_final` decimal(10,2) DEFAULT '0.00',
  `precio_combo` decimal(10,2) DEFAULT '0.00',
  `descuento_combo` decimal(5,2) DEFAULT '0.00',
  PRIMARY KEY (`id_producto`),
  KEY `receta_id` (`receta_id`),
  KEY `producto_padre_id` (`producto_padre_id`)
) ENGINE=MyISAM AUTO_INCREMENT=4 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

-- Volcando datos para la tabla operaciones_dulce_tia.productos: 3 rows
INSERT INTO `productos` (`id_producto`, `nombre_producto`, `tipo_producto`, `categoria`, `precio_venta`, `peso`, `unidad_peso`, `receta_id`, `producto_padre_id`, `descripcion_producto`, `fecha_creacion`, `activo`, `sabor_producto`, `relleno_producto`, `cobertura_producto`, `costo_receta`, `tiempo_preparacion_minutos`, `mano_obra`, `empaques`, `costos_indirectos`, `margen_porcentaje`, `precio_sugerido`, `costo_total`, `precio_final`, `precio_combo`, `descuento_combo`) VALUES
	(1, 'Torta de Vainilla', 'individual', 'Tortas', 0.00, 1.00, 'kg', 1, NULL, '', '2026-07-30 11:39:05', 1, NULL, NULL, NULL, 0.00, 0.00, 3.60, 0.00, 0.06, 40.00, 5.12, 3.66, 5.12, NULL, 0.00),
	(2, 'Suspiros', 'individual', 'Postres', 0.00, 1.00, 'kg', 2, NULL, '', '2026-07-30 11:43:05', 0, NULL, NULL, NULL, 0.00, 0.00, 0.30, 0.00, 0.00, 40.00, 0.42, 0.30, 0.42, NULL, 0.00),
	(3, 'Suspiros', 'individual', 'Postres', 0.00, 1.00, 'kg', 3, NULL, '', '2026-07-30 18:11:32', 1, NULL, NULL, NULL, 0.00, 0.00, 0.63, 0.00, 0.01, 40.00, 0.90, 0.64, 0.90, NULL, 0.00);

/*!40103 SET TIME_ZONE=IFNULL(@OLD_TIME_ZONE, 'system') */;
/*!40101 SET SQL_MODE=IFNULL(@OLD_SQL_MODE, '') */;
/*!40014 SET FOREIGN_KEY_CHECKS=IFNULL(@OLD_FOREIGN_KEY_CHECKS, 1) */;
/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40111 SET SQL_NOTES=IFNULL(@OLD_SQL_NOTES, 1) */;
