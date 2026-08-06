"""
============================================================
Sistema La Dulce Tía

Archivo:
    reporte_service.py

Responsabilidad:
    Servicio de generación de reportes y exportación a PDF.

Autor:
    Proyecto La Dulce Tía
============================================================
"""

from __future__ import annotations

import io
from datetime import datetime
from typing import Any, Dict, List, Optional

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.platypus import (
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)

from ui.core.services.base.service_result import ServiceResult
from ui.core.repositories.operaciones.reporte_repository import ReporteRepository


class ReporteService:
    """
    Servicio para generar reportes históricos y exportarlos a PDF.
    """

    # Mapeo de tipos de reporte a nombres amigables
    TIPOS = {
        "ingredientes": "Historial de Ingredientes (Lotes)",
        "ventas": "Historial de Ventas",
        "produccion": "Historial de Producción",
        "mermas": "Historial de Mermas",
    }

    def __init__(self, repository: ReporteRepository):
        self._repo = repository

    # ============================================================
    # OBTENCIÓN DE DATOS (delega al repositorio)
    # ============================================================
    def obtener_datos(
        self,
        tipo: str,
        fecha_inicio: Optional[str] = None,
        fecha_fin: Optional[str] = None,
    ) -> ServiceResult:
        """
        Obtiene los datos históricos según el tipo de reporte.
        """
        try:
            if tipo == "ingredientes":
                datos = self._repo.obtener_historial_ingredientes(fecha_inicio, fecha_fin)
            elif tipo == "ventas":
                datos = self._repo.obtener_historial_ventas(fecha_inicio, fecha_fin)
            elif tipo == "produccion":
                datos = self._repo.obtener_historial_produccion(fecha_inicio, fecha_fin)
            elif tipo == "mermas":
                datos = self._repo.obtener_historial_mermas(fecha_inicio, fecha_fin)
            else:
                return ServiceResult.error(f"Tipo de reporte no soportado: {tipo}")

            return ServiceResult.ok(datos=datos)
        except Exception as e:
            return ServiceResult.error(f"Error al obtener datos: {e}")

    # ============================================================
    # GENERACIÓN DE PDF
    # ============================================================
    def generar_pdf(
        self,
        tipo: str,
        datos: List[Dict[str, Any]],
        fecha_inicio: Optional[str] = None,
        fecha_fin: Optional[str] = None,
    ) -> ServiceResult:
        """
        Genera un PDF con los datos proporcionados y el título correspondiente.
        Devuelve los bytes del PDF.
        """
        if not datos:
            return ServiceResult.error("No hay datos para generar el PDF.")

        titulo = self.TIPOS.get(tipo, "Reporte")
        subtitulo = f"Período: {fecha_inicio or 'Inicio'} al {fecha_fin or 'Fin'}"

        try:
            pdf_bytes = self._crear_pdf(titulo, subtitulo, datos, tipo)
            return ServiceResult.ok(datos=pdf_bytes)
        except Exception as e:
            return ServiceResult.error(f"Error al generar PDF: {e}")

    def _crear_pdf(self, titulo: str, subtitulo: str, datos: List[Dict], tipo: str) -> bytes:
        """
        Construye el documento PDF usando reportlab.
        """
        buffer = io.BytesIO()
        # Todas las tablas de reportes tienen 7 columnas con texto largo
        # (responsable, motivo, cliente, etc.); en A4 vertical no entran
        # sin comprimirse o cortarse, por eso se usa horizontal (landscape).
        doc = SimpleDocTemplate(
            buffer,
            pagesize=landscape(A4),
            leftMargin=1.5*cm,
            rightMargin=1.5*cm,
            topMargin=2*cm,
            bottomMargin=2*cm,
        )

        # Estilos
        estilos = getSampleStyleSheet()
        estilo_titulo = ParagraphStyle(
            'TituloReporte',
            parent=estilos['Heading1'],
            fontSize=18,
            alignment=1,  # centrado
            spaceAfter=6,
        )
        estilo_subtitulo = ParagraphStyle(
            'SubtituloReporte',
            parent=estilos['Normal'],
            fontSize=12,
            alignment=1,
            textColor=colors.grey,
            spaceAfter=12,
        )
        estilo_fecha = ParagraphStyle(
            'FechaReporte',
            parent=estilos['Normal'],
            fontSize=10,
            alignment=2,  # derecha
            textColor=colors.grey,
            spaceAfter=12,
        )

        # Encabezado
        elementos = []
        elementos.append(Paragraph(titulo, estilo_titulo))
        elementos.append(Paragraph(subtitulo, estilo_subtitulo))
        elementos.append(Paragraph(f"Generado: {datetime.now().strftime('%d/%m/%Y %H:%M')}", estilo_fecha))
        elementos.append(Spacer(1, 0.5*cm))

        # Construir la tabla según el tipo
        tabla = self._construir_tabla(tipo, datos)
        if tabla:
            elementos.append(tabla)

        # Pie de página (opcional, se añade en el doc template)
        doc.build(elementos)
        buffer.seek(0)
        return buffer.read()

    def _construir_tabla(self, tipo: str, datos: List[Dict]) -> Optional[Table]:
        """
        Construye una tabla de reportlab con los datos según el tipo.

        Nota: se usa `d.get(campo) or valor_por_defecto` en vez de
        `d.get(campo, valor_por_defecto)`. La diferencia importa cuando
        la columna existe en la fila pero su valor en la base de datos
        es NULL: `dict.get` solo aplica el default si la clave NO
        existe, así que con NULL explícito devolvería None y el
        formato f"{...:.2f}" fallaría con TypeError.
        """
        if tipo == "ingredientes":
            encabezados = ["Ingrediente", "Lote", "Stock Actual", "Unidad", "Costo Unitario", "Ingreso", "Caducidad"]
            anchos = [5.5*cm, 1.8*cm, 2.8*cm, 2.2*cm, 3*cm, 3*cm, 3*cm]
            datos_tabla = [
                [
                    d.get('nombre_ingrediente') or '',
                    d.get('id_lote') if d.get('id_lote') is not None else '',
                    f"{float(d.get('stock_actual') or 0):.2f}",
                    d.get('unidad_medida') or '',
                    f"${float(d.get('costo_unitario') or 0):.2f}",
                    d.get('fecha_ingreso') or '',
                    d.get('fecha_caducidad') or '',
                ]
                for d in datos
            ]
        elif tipo == "ventas":
            encabezados = ["ID Venta", "Fecha", "Cliente", "Subtotal", "Descuento", "Total", "Estado"]
            anchos = [2.2*cm, 3.2*cm, 6*cm, 2.8*cm, 2.8*cm, 2.8*cm, 3*cm]
            datos_tabla = [
                [
                    d.get('id_venta') if d.get('id_venta') is not None else '',
                    d.get('fecha_venta') or '',
                    d.get('cliente_nombre') or '',
                    f"${float(d.get('subtotal') or 0):.2f}",
                    f"${float(d.get('descuento') or 0):.2f}",
                    f"${float(d.get('total') or 0):.2f}",
                    d.get('estado') or '',
                ]
                for d in datos
            ]
        elif tipo == "produccion":
            encabezados = ["N° Orden", "Fecha Planif.", "Estado", "Prioridad", "Responsable", "Costo Real", "Tiempo Real"]
            anchos = [3*cm, 3*cm, 3*cm, 2.8*cm, 5*cm, 3*cm, 3*cm]
            datos_tabla = [
                [
                    d.get('numero_orden') or '',
                    d.get('fecha_planificada') or '',
                    d.get('estado') or '',
                    d.get('prioridad') or '',
                    d.get('responsable') or '',
                    f"${float(d.get('costo_real') or 0):.2f}",
                    f"{d.get('tiempo_real_minutos') or 0} min",
                ]
                for d in datos
            ]
        elif tipo == "mermas":
            encabezados = ["Fecha", "Cantidad", "Unidad", "Tipo", "Motivo", "Costo Asociado", "Producto/Ingrediente"]
            anchos = [3*cm, 2.5*cm, 2.2*cm, 3.5*cm, 4*cm, 3*cm, 4.5*cm]
            datos_tabla = [
                [
                    d.get('fecha_registro') or '',
                    f"{float(d.get('cantidad') or 0):.2f}",
                    d.get('unidad') or '',
                    d.get('tipo_merma') or '',
                    d.get('motivo') or '',
                    f"${float(d.get('costo_asociado') or 0):.2f}",
                    d.get('producto_asociado') or '',
                ]
                for d in datos
            ]
        else:
            return None

        # Agregar encabezados como primera fila
        tabla_datos = [encabezados] + datos_tabla

        # Estilo de la tabla (con anchos fijos para que no se compriman
        # ni se corten las columnas de texto largo en horizontal)
        tabla = Table(tabla_datos, colWidths=anchos, repeatRows=1, hAlign='CENTER')
        estilo_tabla = TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 10),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 6),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
            ('FONTSIZE', (0, 1), (-1, -1), 9),
            ('TOPPADDING', (0, 1), (-1, -1), 4),
            ('BOTTOMPADDING', (0, 1), (-1, -1), 4),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ])
        # Alternar colores de filas
        for i in range(1, len(tabla_datos), 2):
            estilo_tabla.add('BACKGROUND', (0, i), (-1, i), colors.lightgrey)
        tabla.setStyle(estilo_tabla)

        return tabla