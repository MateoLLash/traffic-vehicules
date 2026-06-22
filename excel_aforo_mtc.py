"""
excel_aforo_mtc.py - Generador de Excel para aforos vehiculares MTC

Genera reportes en formato oficial del Ministerio de Transportes de Perú
para estudios de tráfico, con clasificación vehicular cada 15 minutos.
"""

import openpyxl
from openpyxl.styles import (Font, PatternFill, Alignment, Border, Side,
                             Protection, NamedStyle)
from openpyxl.utils import get_column_letter
from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Optional
import os

from utils import setup_logger

# Configurar logger
logger = setup_logger('excel_aforo_mtc')

# Tipos de vehículos según clasificación MTC
VEHICLE_TYPES_MTC = [
    'Auto', 'Moto', 'Bus', 'Microbus', 'Omnibus',
    'Omnibus Articulado', 'Camion', 'Camioneta',
    'Combi', 'Furgon', 'Minivan', 'Van',
    'Mototaxi', 'Trailer', 'Trailer Doble', 'Especiales', 'Peaton'
]

# Direcciones cardinales para el formato
DIRECCIONES = ['N-S', 'S-N', 'E-O', 'O-E']


class ExcelAforoMTC:
    """
    Generador de Excel para aforos vehiculares en formato MTC.
    
    Attributes:
        workbook: Libro de Excel
        estacion: Nombre de la estación de aforo
        codigo: Código de la estación
        tramo: Tramo de la carretera
        ubicacion: Ubicación específica
        sentido: Sentido de circulación
        dia: Día de la semana
        fecha: Fecha del aforo
        interval_minutes: Intervalo de conteo (default: 15)
    """
    
    def __init__(self,
                 estacion: str,
                 codigo: str,
                 tramo: str,
                 ubicacion: str,
                 sentido: str,
                 dia: str,
                 fecha: datetime,
                 interval_minutes: int = 15):
        """
        Inicializa el generador de Excel MTC.
        
        Args:
            estacion: Nombre de la estación
            codigo: Código de la estación
            tramo: Tramo de carretera
            ubicacion: Ubicación específica
            sentido: Sentido de circulación
            dia: Día de la semana (ej: 'Lunes')
            fecha: Fecha del aforo
            interval_minutes: Intervalo en minutos (15 por defecto)
        """
        self.workbook = openpyxl.Workbook()
        self.workbook.remove(self.workbook.active)
        
        self.estacion = estacion
        self.codigo = codigo
        self.tramo = tramo
        self.ubicacion = ubicacion
        self.sentido = sentido
        self.dia = dia
        self.fecha = fecha
        self.interval_minutes = interval_minutes
        
        # Tipos de vehículos a registrar
        self.vehicle_types = VEHICLE_TYPES_MTC
        
        # Estilos predefinidos
        self._init_styles()
        
        logger.info(f"Generador de Excel MTC inicializado: {estacion}")
    
    def _init_styles(self):
        """Inicializa los estilos para el Excel."""
        # Colores institucionales MTC
        self.color_header = "1F4E78"  # Azul oscuro
        self.color_subheader = "2E75B6"  # Azul medio
        self.color_total = "FFC000"  # Amarillo
        self.color_alt_row = "E9ECEF"  # Gris claro
        self.color_border = "B3B3B3"  # Gris para bordes
        
        # Fuentes
        self.font_header = Font(name='Arial', size=10, bold=True, color='FFFFFF')
        self.font_subheader = Font(name='Arial', size=9, bold=True, color='FFFFFF')
        self.font_normal = Font(name='Arial', size=9)
        self.font_bold = Font(name='Arial', size=9, bold=True)
        self.font_total = Font(name='Arial', size=9, bold=True, color='000000')
        
        # Rellenos
        self.fill_header = PatternFill(start_color=self.color_header,
                                      end_color=self.color_header,
                                      fill_type='solid')
        self.fill_subheader = PatternFill(start_color=self.color_subheader,
                                         end_color=self.color_subheader,
                                         fill_type='solid')
        self.fill_total = PatternFill(start_color=self.color_total,
                                     end_color=self.color_total,
                                     fill_type='solid')
        self.fill_alt = PatternFill(start_color=self.color_alt_row,
                                   end_color=self.color_alt_row,
                                   fill_type='solid')
        
        # Bordes
        thin_side = Side(style='thin', color=self.color_border)
        self.border_all = Border(left=thin_side, right=thin_side,
                                top=thin_side, bottom=thin_side)
        self.border_bottom = Border(bottom=thin_side)
        
        # Alineaciones
        self.align_center = Alignment(horizontal='center', vertical='center',
                                     wrap_text=True)
        self.align_left = Alignment(horizontal='left', vertical='center')
        self.align_right = Alignment(horizontal='right', vertical='center')
    
    def generate(self,
                data_by_line: dict,
                output_path: str,
                supervisor: str = "",
                coordinador: str = "") -> str:

        ws = self.workbook.create_sheet("Aforo Vehicular")
        self._write_header(ws)
        self._write_count_table_multiline(ws, data_by_line)
        self._write_totals_section_multiline(ws, data_by_line)
        self._write_signatures(ws, supervisor, coordinador)
        self._apply_formatting(ws)
        self.workbook.save(output_path)
        logger.info(f"Excel MTC guardado: {output_path}")
        return output_path
    
    def _write_header(self, ws):
        """Escribe el encabezado de identificación del aforo."""
        row = 1
        
        # Título principal
        ws.merge_cells(f'A{row}:M{row}')
        cell = ws[f'A{row}']
        cell.value = "REGISTRO DE AFORO VEHICULAR - MTC"
        cell.font = Font(name='Arial', size=14, bold=True, color='FFFFFF')
        cell.fill = self.fill_header
        cell.alignment = self.align_center
        row += 1
        
        # Información de la estación (2 columnas)
        info_data = [
            ("ESTACIÓN:", self.estacion, "CÓDIGO:", self.codigo),
            ("TRAMO:", self.tramo, "UBICACIÓN:", self.ubicacion),
            ("SENTIDO:", self.sentido, "DÍA:", self.dia),
            ("FECHA:", self.fecha.strftime('%d/%m/%Y'), "INTERVALO:", f"{self.interval_minutes} min"),
        ]
        
        for info_row in info_data:
            # Columna 1 (A)
            ws[f'A{row}'] = info_row[0]
            ws[f'A{row}'].font = self.font_bold
            ws[f'B{row}'] = info_row[1]
            ws[f'B{row}'].font = self.font_normal
            
            # Columna 2 (D)
            ws[f'D{row}'] = info_row[2]
            ws[f'D{row}'].font = self.font_bold
            ws[f'E{row}'] = info_row[3]
            ws[f'E{row}'].font = self.font_normal
            
            row += 1
        
        # Espacio después del encabezado
        row += 1
        
        return row
    
    def _write_count_table_multiline(self, ws, data_by_line: dict):
        start_row  = 9
        line_names = list(data_by_line.keys())
        n_lines    = len(line_names)

        all_intervals = sorted(set(
            interval
            for line_data in data_by_line.values()
            for interval in line_data.keys()
        ))

        # ── Fila 1 encabezado: HORA | Auto(merge) | Moto(merge) | ... | TOTAL ──
        ws[f'A{start_row}']           = "HORA"
        ws[f'A{start_row}'].font      = self.font_header
        ws[f'A{start_row}'].fill      = self.fill_header
        ws[f'A{start_row}'].alignment = self.align_center
        ws.row_dimensions[start_row].height = 28

        col = 2
        for vt in self.vehicle_types:
            col_start_letter = get_column_letter(col)
            col_end_letter   = get_column_letter(col + n_lines - 1)
            if n_lines > 1:
                ws.merge_cells(f'{col_start_letter}{start_row}:{col_end_letter}{start_row}')
            cell           = ws[f'{col_start_letter}{start_row}']
            cell.value     = vt
            cell.font      = self.font_header
            cell.fill      = self.fill_header
            cell.alignment = self.align_center
            cell.border    = self.border_all
            col += n_lines

        col_total        = col
        col_total_letter = get_column_letter(col_total)
        ws[f'{col_total_letter}{start_row}']           = "TOTAL"
        ws[f'{col_total_letter}{start_row}'].font      = self.font_header
        ws[f'{col_total_letter}{start_row}'].fill      = self.fill_total
        ws[f'{col_total_letter}{start_row}'].alignment = self.align_center
        ws.column_dimensions[col_total_letter].width   = 10

        # ── Fila 2 sub-encabezado: vacío | L0 L1 | L0 L1 | ... ──
        sub_row = start_row + 1
        ws[f'A{sub_row}'].fill = self.fill_subheader

        col = 2
        for _ in self.vehicle_types:
            for line_name in line_names:
                col_letter                             = get_column_letter(col)
                short                                  = line_name.split('_')[-1] if '_' in line_name else line_name
                ws[f'{col_letter}{sub_row}']           = short
                ws[f'{col_letter}{sub_row}'].font      = self.font_subheader
                ws[f'{col_letter}{sub_row}'].fill      = self.fill_subheader
                ws[f'{col_letter}{sub_row}'].alignment = self.align_center
                ws[f'{col_letter}{sub_row}'].border    = self.border_all
                ws.column_dimensions[col_letter].width = 10
                col += 1

        ws[f'{col_total_letter}{sub_row}']           = "TOT"
        ws[f'{col_total_letter}{sub_row}'].font      = self.font_subheader
        ws[f'{col_total_letter}{sub_row}'].fill      = self.fill_total
        ws[f'{col_total_letter}{sub_row}'].alignment = self.align_center

        # ── Filas de datos ──
        data_start = sub_row + 1

        for i, interval in enumerate(all_intervals):
            row       = data_start + i
            fill_row  = self.fill_alt if i % 2 == 1 else None

            ws[f'A{row}']           = interval
            ws[f'A{row}'].font      = self.font_normal
            ws[f'A{row}'].alignment = self.align_center
            ws[f'A{row}'].border    = self.border_all
            if fill_row:
                ws[f'A{row}'].fill = fill_row

            col       = 2
            row_total = 0

            for vt in self.vehicle_types:
                for line_name in line_names:
                    counts     = data_by_line[line_name].get(interval, {v: 0 for v in self.vehicle_types})
                    val        = counts.get(vt, 0)
                    col_letter = get_column_letter(col)
                    ws[f'{col_letter}{row}']           = val if val > 0 else ''
                    ws[f'{col_letter}{row}'].font      = self.font_normal
                    ws[f'{col_letter}{row}'].alignment = self.align_center
                    ws[f'{col_letter}{row}'].border    = self.border_all
                    if fill_row:
                        ws[f'{col_letter}{row}'].fill  = fill_row
                    row_total += val
                    col       += 1

            ws[f'{col_total_letter}{row}']           = row_total
            ws[f'{col_total_letter}{row}'].font      = self.font_bold
            ws[f'{col_total_letter}{row}'].alignment = self.align_center
            ws[f'{col_total_letter}{row}'].border    = self.border_all
            if fill_row:
                ws[f'{col_total_letter}{row}'].fill  = fill_row

        # ── Fila TOTALES ──
        total_row = data_start + len(all_intervals)
        ws[f'A{total_row}']           = "TOTALES"
        ws[f'A{total_row}'].font      = self.font_bold
        ws[f'A{total_row}'].fill      = self.fill_total
        ws[f'A{total_row}'].alignment = self.align_center
        ws[f'A{total_row}'].border    = self.border_all

        col         = 2
        grand_total = 0

        for vt in self.vehicle_types:
            for line_name in line_names:
                col_letter  = get_column_letter(col)
                line_vt_sum = sum(
                    data_by_line[line_name].get(iv, {}).get(vt, 0)
                    for iv in all_intervals
                )
                ws[f'{col_letter}{total_row}']           = line_vt_sum if line_vt_sum > 0 else ''
                ws[f'{col_letter}{total_row}'].font      = self.font_bold
                ws[f'{col_letter}{total_row}'].fill      = self.fill_total
                ws[f'{col_letter}{total_row}'].alignment = self.align_center
                ws[f'{col_letter}{total_row}'].border    = self.border_all
                grand_total += line_vt_sum
                col         += 1

        ws[f'{col_total_letter}{total_row}']           = grand_total
        ws[f'{col_total_letter}{total_row}'].font      = self.font_bold
        ws[f'{col_total_letter}{total_row}'].fill      = self.fill_total
        ws[f'{col_total_letter}{total_row}'].alignment = self.align_center
        ws[f'{col_total_letter}{total_row}'].border    = self.border_all

        self._table_end_row = total_row

        obs_row                = total_row + 2
        ws[f'A{obs_row}']      = "OBSERVACIONES:"
        ws[f'A{obs_row}'].font = self.font_bold

    def _write_totals_section_multiline(self, ws, data_by_line: dict):
        row = self._table_end_row + 4

        ws.merge_cells(f'A{row}:C{row}')
        ws[f'A{row}']           = "RESUMEN DE TOTALES POR LÍNEA Y TIPO"
        ws[f'A{row}'].font      = Font(name='Arial', size=10, bold=True)
        ws[f'A{row}'].alignment = self.align_left
        row += 1

        for line_name, line_data in data_by_line.items():
            ws[f'A{row}']      = f"— {line_name}"
            ws[f'A{row}'].font = Font(name='Arial', size=9, bold=True,
                                    color=self.color_subheader)
            row += 1

            totals = {vt: 0 for vt in self.vehicle_types}
            for interval_counts in line_data.values():
                for vt, cnt in interval_counts.items():
                    if vt in totals:
                        totals[vt] += cnt

            items = [(vt, cnt) for vt, cnt in totals.items() if cnt > 0]
            half  = (len(items) + 1) // 2

            for i in range(max(half, 1)):
                if i < len(items):
                    ws[f'A{row}']      = items[i][0]
                    ws[f'B{row}']      = items[i][1]
                    ws[f'A{row}'].font = self.font_normal
                    ws[f'B{row}'].font = self.font_bold
                j = i + half
                if j < len(items):
                    ws[f'D{row}']      = items[j][0]
                    ws[f'E{row}']      = items[j][1]
                    ws[f'D{row}'].font = self.font_normal
                    ws[f'E{row}'].font = self.font_bold
                row += 1
            row += 1
        
        # Total general
        total_general = sum(
            cnt
            for line_data in data_by_line.values()
            for interval_counts in line_data.values()
            for cnt in interval_counts.values()
        )
        row += 1
        ws[f'A{row}'] = "TOTAL GENERAL:"
        ws[f'A{row}'].font = Font(name='Arial', size=10, bold=True)
        ws[f'B{row}'] = total_general
        ws[f'B{row}'].font = Font(name='Arial', size=10, bold=True)
        ws[f'B{row}'].fill = self.fill_total
    
    def _write_signatures(self, ws, supervisor: str, coordinador: str):
        """Escribe la sección de firmas al final del reporte."""
        row = self._table_end_row + 9
        
        # Línea separadora
        ws.merge_cells(f'A{row}:M{row}')
        ws[f'A{row}'] = "__________________________________________________"
        ws[f'A{row}'].alignment = self.align_center
        row += 1
        
        # Firmas en 2 columnas
        # Supervisor
        ws[f'A{row}'] = "SUPERVISOR:"
        ws[f'A{row}'].font = self.font_bold
        ws[f'B{row}'] = supervisor if supervisor else "__________________"
        ws[f'B{row}'].font = self.font_normal
        
        # Coordinador
        ws[f'G{row}'] = "COORDINADOR:"
        ws[f'G{row}'].font = self.font_bold
        ws[f'H{row}'] = coordinador if coordinador else "__________________"
        ws[f'H{row}'].font = self.font_normal
        
        row += 1
        
        # Fecha de firma
        ws[f'A{row}'] = f"Fecha: {datetime.now().strftime('%d/%m/%Y')}"
        ws[f'A{row}'].font = Font(name='Arial', size=8, italic=True)
        ws[f'G{row}'] = f"Fecha: {datetime.now().strftime('%d/%m/%Y')}"
        ws[f'G{row}'].font = Font(name='Arial', size=8, italic=True)
    
    def _apply_formatting(self, ws):
        """Aplica formato general a la hoja."""
        # Anchos de columna
        ws.column_dimensions['A'].width = 18  # Hora
        ws.column_dimensions['B'].width = 12  # Sentido
        
        # Bordes a toda la tabla
        for row in ws.iter_rows(min_row=9, max_row=self._table_end_row):
            for cell in row:
                if cell.value is not None or cell.column <= 12:
                    cell.border = self.border_all
        
        # Congelar paneles en la fila 9
        ws.freeze_panes = 'A10'
    
    def generate_from_consolidator(self, 
                                   consolidator,
                                   output_path: str,
                                   supervisor: str = "",
                                   coordinador: str = "") -> str:
        """
        Genera el Excel a partir de un objeto TrafficConsolidator.
        
        Args:
            consolidator: Objeto TrafficConsolidator con datos procesados
            output_path: Ruta de salida
            supervisor: Nombre del supervisor
            coordinador: Nombre del coordinador
            
        Returns:
            Ruta del archivo generado
        """
        # Extraer datos del consolidator
        consolidated = consolidator.get_consolidated_counts()
        intervals = consolidated['intervals']
        counts = consolidated['counts']
        
        # Convertir a formato de 15 minutos
        data_15min = {}
        
        for idx, (interval_start, interval_end) in enumerate(intervals):
            time_str = interval_start.strftime('%H:%M')
            
            # Inicializar conteos para este intervalo
            interval_counts = {vt: 0 for vt in self.vehicle_types}
            
            # Agregar conteos de este intervalo
            if idx in counts:
                for class_name, turn_counts in counts[idx].items():
                    # Mapear nombre de clase a tipo MTC
                    mtc_type = self._map_to_mtc_type(class_name)
                    if mtc_type in interval_counts:
                        interval_counts[mtc_type] += sum(turn_counts.values())
            
            data_15min[time_str] = interval_counts
        
        # Generar Excel
        return self.generate(data_15min, output_path, supervisor, coordinador)
    
    def _map_to_mtc_type(self, class_name: str) -> str:
        """
        Mapea nombres de clases del sistema a tipos MTC.
        
        Args:
            class_name: Nombre de la clase (ej: 'Auto', 'Moto')
            
        Returns:
            Tipo MTC correspondiente
        """
        # Mapeo directo
        mapping = {
            'Auto': 'Auto',
            'Moto': 'Moto lineal',
            'Moto lineal': 'Moto lineal',
            'Bus': 'Microbús',
            'Microbús': 'Microbús',
            'Camión': 'Camión',
            'Camioneta': 'Camioneta Rural',
            'Camioneta Rural': 'Camioneta Rural',
            'Mototaxi': 'Mototaxi',
            'Carreta': 'Carreta',
            'Bicicleta': 'Bicicleta',
            'Scooter': 'Scooter',
            'Peatón': 'Peatón',  # Aunque no está en la lista oficial, lo mantenemos
        }
        
        return mapping.get(class_name, class_name)
    
    def save(self, filename: str) -> str:
        """Guarda el libro de Excel."""
        self.workbook.save(filename)
        logger.info(f"Excel guardado: {filename}")
        return filename


# ─── FUNCIÓN DE CONVENIENCIA ─────────────────────────────────────

def generar_reporte_mtc(consolidator,
                        estacion: str,
                        codigo: str,
                        tramo: str,
                        ubicacion: str,
                        sentido: str,
                        dia: str,
                        fecha: datetime,
                        output_dir: str,
                        supervisor: str = "",
                        coordinador: str = "") -> str:
    """
    Función de conveniencia para generar un reporte MTC.
    
    Args:
        consolidator: Objeto TrafficConsolidator con datos
        estacion: Nombre de la estación
        codigo: Código de la estación
        tramo: Tramo de carretera
        ubicacion: Ubicación específica
        sentido: Sentido de circulación
        dia: Día de la semana
        fecha: Fecha del aforo
        output_dir: Directorio de salida
        supervisor: Nombre del supervisor
        coordinador: Nombre del coordinador
        
    Returns:
        Ruta del archivo generado
    """
    # Crear directorio si no existe
    os.makedirs(output_dir, exist_ok=True)
    
    # Nombre del archivo
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"Aforo_{codigo}_{fecha.strftime('%Y%m%d')}_{timestamp}.xlsx"
    output_path = os.path.join(output_dir, filename)
    
    # Crear generador
    generator = ExcelAforoMTC(
        estacion=estacion,
        codigo=codigo,
        tramo=tramo,
        ubicacion=ubicacion,
        sentido=sentido,
        dia=dia,
        fecha=fecha
    )
    
    # Generar reporte
    return generator.generate_from_consolidator(
        consolidator,
        output_path,
        supervisor,
        coordinador
    )


# ─── EJEMPLO DE USO ─────────────────────────────────────────────

if __name__ == "__main__":
    from consolidator import TrafficConsolidator
    
    print("=== Prueba del Generador MTC ===\n")
    
    # Crear datos de prueba
    consolidator = TrafficConsolidator(
        intersection_name="Av. República de Panamá con Vía Expresa",
        session_date=datetime(2024, 3, 15, 6, 0, 0),
        interval_minutes=15
    )
    
    # Agregar segmentos de prueba
    for i in range(4):
        start_time = datetime(2024, 3, 15, 6, 0, 0) + timedelta(minutes=i * 15)
        
        test_crossings = [
            {
                'timestamp': 30.0,
                'class_spanish': 'Auto',
                'direction': 'up_to_down',
                'track_id': f'track_{i}_1',
                'turn_number': 1
            },
            {
                'timestamp': 45.0,
                'class_spanish': 'Moto',
                'direction': 'up_to_down',
                'track_id': f'track_{i}_2',
                'turn_number': 1
            }
        ]
        
        test_stats = {
            'elapsed_time': 300,
            'total_crossings': 2
        }
        
        consolidator.add_segment(
            video_name=f"video_segment_{i+1}.mp4",
            start_time=start_time,
            crossings=test_crossings,
            statistics=test_stats
        )
    
    # Generar reporte MTC
    output_dir = "outputs/reportes_mtc"
    
    reporte = generar_reporte_mtc(
        consolidator=consolidator,
        estacion="Av. República de Panamá - Vía Expresa",
        codigo="MTC-001-2024",
        tramo="Km 3.2 - Km 4.8",
        ubicacion="Intersección con Vía Expresa",
        sentido="N-S",
        dia="Viernes",
        fecha=datetime(2024, 3, 15),
        output_dir=output_dir,
        supervisor="Ing. Carlos Pérez",
        coordinador="Ing. María Gonzales"
    )
    
    print(f"✅ Reporte generado: {reporte}")
    print("\n✓ Módulo Excel MTC funcionando correctamente")