"""
consolidator.py - Módulo de consolidación de múltiples videos

Este módulo consolida los resultados de múltiples videos procesados
de la misma intersección en una única estructura de datos para
generar reportes unificados de 3-24 horas.
"""

import json
import os
from typing import List, Dict, Optional, Tuple
from datetime import datetime, timedelta
from collections import defaultdict
import numpy as np

from utils import setup_logger

# Configurar logger
logger = setup_logger('consolidator')


class VideoSegment:
    """
    Representa un segmento de video procesado
    
    Attributes:
        video_name: Nombre del archivo de video
        start_time: Tiempo de inicio del segmento (datetime)
        duration: Duración en segundos
        crossings: Lista de cruces detectados
        statistics: Estadísticas del segmento
    """
    
    def __init__(self,
                 video_name: str,
                 start_time: datetime,
                 duration: float,
                 crossings: List[Dict],
                 statistics: Dict):
        """
        Inicializa un segmento de video
        
        Args:
            video_name: Nombre del video
            start_time: Fecha/hora de inicio
            duration: Duración en segundos
            crossings: Lista de cruces
            statistics: Estadísticas del video
        """
        self.video_name = video_name
        self.start_time = start_time
        self.duration = duration
        self.crossings = crossings
        self.statistics = statistics
        self.end_time = start_time + timedelta(seconds=duration)
    
    def get_absolute_timestamps(self) -> List[Dict]:
        """
        Convierte timestamps relativos a absolutos
        
        Returns:
            Lista de cruces con timestamps absolutos
        """
        absolute_crossings = []
        for crossing in self.crossings:
            crossing_copy = crossing.copy()
            relative_time = crossing['timestamp']
            absolute_time = self.start_time + timedelta(seconds=relative_time)
            crossing_copy['absolute_timestamp'] = absolute_time
            crossing_copy['video_segment'] = self.video_name
            absolute_crossings.append(crossing_copy)
        
        return absolute_crossings


class TrafficConsolidator:
    """
    Consolidador de múltiples videos de tráfico
    
    Consolida datos de múltiples segmentos de video de la misma
    intersección en un reporte unificado de 3-24 horas.
    
    Attributes:
        intersection_name: Nombre de la intersección
        session_date: Fecha de la sesión
        segments: Lista de segmentos de video
        interval_minutes: Intervalo de agrupación (default: 15 min)
    """
    
    def __init__(self,
                 intersection_name: str,
                 session_date: datetime,
                 interval_minutes: int = 15):
        """
        Inicializa el consolidador
        
        Args:
            intersection_name: Nombre de la intersección
            session_date: Fecha de inicio de la sesión
            interval_minutes: Intervalo de agrupación en minutos
        """
        self.intersection_name = intersection_name
        self.session_date = session_date
        self.interval_minutes = interval_minutes
        self.segments = []
        
        logger.info(f"Consolidador inicializado: {intersection_name} - "
                   f"Intervalo: {interval_minutes} min")
    
    def add_segment(self,
                   video_name: str,
                   start_time: datetime,
                   crossings: List[Dict],
                   statistics: Dict,
                   duration: float = None) -> VideoSegment:
        """
        Agrega un segmento de video procesado
        
        Args:
            video_name: Nombre del archivo de video
            start_time: Fecha/hora de inicio del video
            crossings: Lista de cruces detectados
            statistics: Estadísticas del video
            duration: Duración en segundos (calculada si no se proporciona)
            
        Returns:
            Segmento creado
        """
        # Calcular duración si no se proporciona
        if duration is None:
            duration = statistics.get('elapsed_time', 0)
        
        segment = VideoSegment(video_name, start_time, duration, 
                              crossings, statistics)
        self.segments.append(segment)
        
        logger.info(f"Segmento agregado: {video_name} - "
                   f"Duración: {duration:.1f}s - "
                   f"Cruces: {len(crossings)}")
        
        return segment
    
    def get_session_duration(self) -> float:
        """
        Obtiene la duración total de la sesión en segundos
        
        Returns:
            Duración en segundos
        """
        if not self.segments:
            return 0
        
        start = min(seg.start_time for seg in self.segments)
        end = max(seg.end_time for seg in self.segments)
        
        return (end - start).total_seconds()
    
    def get_all_crossings(self) -> List[Dict]:
        """
        Obtiene todos los cruces de todos los segmentos con timestamps absolutos
        
        Returns:
            Lista consolidada de cruces
        """
        all_crossings = []
        
        for segment in self.segments:
            all_crossings.extend(segment.get_absolute_timestamps())
        
        # Ordenar por timestamp absoluto
        all_crossings.sort(key=lambda x: x['absolute_timestamp'])
        
        return all_crossings
    
    def get_time_intervals(self) -> List[Tuple[datetime, datetime]]:
        """
        Genera intervalos de tiempo para la sesión completa
        
        Returns:
            Lista de tuplas (inicio, fin) para cada intervalo
        """
        if not self.segments:
            return []
        
        # Obtener rango de tiempo
        start_time = min(seg.start_time for seg in self.segments)
        end_time = max(seg.end_time for seg in self.segments)
        
        # Redondear inicio al intervalo anterior
        minutes_to_subtract = start_time.minute % self.interval_minutes
        interval_start = start_time - timedelta(minutes=minutes_to_subtract)
        interval_start = interval_start.replace(second=0, microsecond=0)
        
        # Generar intervalos
        intervals = []
        current = interval_start
        
        while current <= end_time:
            interval_end = current + timedelta(minutes=self.interval_minutes)
            intervals.append((current, interval_end))
            current = interval_end
        
        return intervals
    
    def get_consolidated_counts(self) -> Dict:
        """
        Obtiene conteos consolidados de toda la sesión
        
        Returns:
            Diccionario con conteos consolidados por:
            - Intervalo de tiempo
            - Tipo de vehículo/peatón
            - Número de giro/sentido
        """
        all_crossings = self.get_all_crossings()
        intervals = self.get_time_intervals()
        
        if not all_crossings or not intervals:
            return {
                'intervals': [],
                'counts': {},
                'totals': {}
            }
        
        # Estructura: counts[interval_idx][class][turn_number] = count
        counts = defaultdict(lambda: defaultdict(lambda: defaultdict(int)))
        
        # Mapear cruces a intervalos
        for crossing in all_crossings:
            timestamp = crossing['absolute_timestamp']
            class_name = crossing['class_spanish']
            
            # Obtener número de giro/sentido del cruce
            # Por ahora usamos 'direction', pero se reemplazará con turn_number
            turn_number = crossing.get('turn_number', 
                                      self._direction_to_default_number(crossing['direction']))
            
            # Encontrar intervalo correspondiente
            for idx, (interval_start, interval_end) in enumerate(intervals):
                if interval_start <= timestamp < interval_end:
                    counts[idx][class_name][turn_number] += 1
                    break
        
        # Calcular totales
        totals = self._calculate_totals(counts, len(intervals))
        
        return {
            'intervals': intervals,
            'counts': counts,
            'totals': totals,
            'interval_minutes': self.interval_minutes
        }
    
    def _direction_to_default_number(self, direction: str) -> int:
        """
        Convierte dirección a número por defecto (temporal)
        
        Args:
            direction: Dirección (up_to_down, etc.)
            
        Returns:
            Número de giro por defecto
        """
        direction_map = {
            'up_to_down': 1,
            'down_to_up': 2,
            'left_to_right': 3,
            'right_to_left': 4
        }
        return direction_map.get(direction, 1)
    
    def _calculate_totals(self, counts: Dict, num_intervals: int) -> Dict:
        """
        Calcula totales por clase, giro e intervalo
        
        Args:
            counts: Diccionario de conteos
            num_intervals: Número de intervalos
            
        Returns:
            Diccionario con totales
        """
        totals = {
            'by_class': defaultdict(int),
            'by_turn': defaultdict(int),
            'by_interval': defaultdict(int),
            'by_class_and_turn': defaultdict(lambda: defaultdict(int)),
            'grand_total': 0
        }
        
        for interval_idx in range(num_intervals):
            interval_total = 0
            
            for class_name, turns in counts[interval_idx].items():
                for turn_number, count in turns.items():
                    totals['by_class'][class_name] += count
                    totals['by_turn'][turn_number] += count
                    totals['by_class_and_turn'][class_name][turn_number] += count
                    totals['grand_total'] += count
                    interval_total += count
            
            totals['by_interval'][interval_idx] = interval_total
        
        return totals
    
    def calculate_peak_hour(self, counts: Dict) -> Dict:
        """
        Calcula la hora punta (intervalo con mayor tráfico en 1 hora)
        
        Args:
            counts: Diccionario de conteos consolidados
            
        Returns:
            Información de hora punta
        """
        intervals = counts['intervals']
        interval_counts = counts['counts']
        
        if not intervals:
            return None
        
        # Calcular cuántos intervalos componen 1 hora
        intervals_per_hour = 60 // self.interval_minutes
        
        # Calcular suma móvil de 1 hora
        max_count = 0
        peak_start_idx = 0
        
        for i in range(len(intervals) - intervals_per_hour + 1):
            # Sumar conteos de los siguientes N intervalos (1 hora)
            hour_count = 0
            for j in range(i, i + intervals_per_hour):
                for class_counts in interval_counts[j].values():
                    hour_count += sum(class_counts.values())
            
            if hour_count > max_count:
                max_count = hour_count
                peak_start_idx = i
        
        peak_start = intervals[peak_start_idx][0]
        peak_end = intervals[peak_start_idx + intervals_per_hour - 1][1]
        
        return {
            'start_time': peak_start,
            'end_time': peak_end,
            'total_count': max_count,
            'interval_range': (peak_start_idx, peak_start_idx + intervals_per_hour)
        }
    
    def calculate_peak_interval(self, counts: Dict) -> Dict:
        """
        Calcula el intervalo individual con mayor tráfico
        
        Args:
            counts: Diccionario de conteos consolidados
            
        Returns:
            Información del intervalo punta
        """
        intervals = counts['intervals']
        interval_counts = counts['counts']
        totals = counts['totals']['by_interval']
        
        if not intervals:
            return None
        
        # Encontrar intervalo con máximo conteo
        max_idx = max(totals.keys(), key=lambda k: totals[k])
        max_count = totals[max_idx]
        
        return {
            'interval': intervals[max_idx],
            'start_time': intervals[max_idx][0],
            'end_time': intervals[max_idx][1],
            'total_count': max_count,
            'interval_index': max_idx
        }
    
    def get_counts_by_direction(self, counts: Dict) -> Dict:
        """
        Agrupa conteos por sentido principal (N-S, S-N, E-O, O-E)
        
        Args:
            counts: Diccionario de conteos consolidados
            
        Returns:
            Conteos agrupados por dirección
        """
        # Esta función se refinará cuando tengamos el mapeo real de giros
        # Por ahora retorna una estructura básica
        
        by_direction = defaultdict(lambda: defaultdict(int))
        
        for interval_idx, class_counts in counts['counts'].items():
            for class_name, turn_counts in class_counts.items():
                for turn_number, count in turn_counts.items():
                    # Mapeo temporal (se reemplazará con configuración real)
                    direction = self._turn_to_direction(turn_number)
                    by_direction[direction][class_name] += count
        
        return dict(by_direction)
    
    def _turn_to_direction(self, turn_number: int) -> str:
        """
        Convierte número de giro a dirección principal (temporal)
        
        Args:
            turn_number: Número de giro
            
        Returns:
            Dirección (N-S, S-N, etc.)
        """
        # Mapeo temporal básico
        turn_map = {
            1: 'N-S',
            2: 'S-N',
            3: 'E-O',
            4: 'O-E'
        }
        return turn_map.get(turn_number, 'Otros')
    
    def export_to_json(self, output_path: str) -> str:
        """
        Exporta datos consolidados a JSON
        
        Args:
            output_path: Ruta del archivo de salida
            
        Returns:
            Ruta del archivo generado
        """
        consolidated = self.get_consolidated_counts()
        
        # Convertir datetime a string para JSON
        json_data = {
            'intersection': self.intersection_name,
            'session_date': self.session_date.isoformat(),
            'total_duration_seconds': self.get_session_duration(),
            'interval_minutes': self.interval_minutes,
            'segments': [
                {
                    'video_name': seg.video_name,
                    'start_time': seg.start_time.isoformat(),
                    'duration': seg.duration,
                    'total_crossings': len(seg.crossings)
                }
                for seg in self.segments
            ],
            'intervals': [
                {
                    'start': interval[0].isoformat(),
                    'end': interval[1].isoformat()
                }
                for interval in consolidated['intervals']
            ],
            'totals': {
                'by_class': dict(consolidated['totals']['by_class']),
                'by_turn': {
                    str(k): v for k, v in consolidated['totals']['by_turn'].items()
                },
                'grand_total': consolidated['totals']['grand_total']
            }
        }
        
        # Calcular hora punta
        peak_hour = self.calculate_peak_hour(consolidated)
        if peak_hour:
            json_data['peak_hour'] = {
                'start': peak_hour['start_time'].isoformat(),
                'end': peak_hour['end_time'].isoformat(),
                'count': peak_hour['total_count']
            }
        
        peak_interval = self.calculate_peak_interval(consolidated)
        if peak_interval:
            json_data['peak_interval'] = {
                'start': peak_interval['start_time'].isoformat(),
                'end': peak_interval['end_time'].isoformat(),
                'count': peak_interval['total_count']
            }
        
        # Guardar
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(json_data, f, indent=2, ensure_ascii=False)
        
        logger.info(f"Datos consolidados exportados a JSON: {output_path}")
        return output_path
    
    def load_from_json(self, json_path: str):
        """
        Carga datos consolidados desde JSON
        
        Args:
            json_path: Ruta del archivo JSON
        """
        with open(json_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        self.intersection_name = data['intersection']
        self.session_date = datetime.fromisoformat(data['session_date'])
        self.interval_minutes = data['interval_minutes']
        
        logger.info(f"Datos consolidados cargados desde: {json_path}")
    
    def get_summary(self) -> Dict:
        """
        Obtiene resumen de la sesión consolidada
        
        Returns:
            Diccionario con resumen completo
        """
        consolidated = self.get_consolidated_counts()
        peak_hour = self.calculate_peak_hour(consolidated)
        peak_interval = self.calculate_peak_interval(consolidated)
        
        return {
            'intersection': self.intersection_name,
            'session_date': self.session_date,
            'total_segments': len(self.segments),
            'total_duration_seconds': self.get_session_duration(),
            'total_duration_hours': self.get_session_duration() / 3600,
            'interval_minutes': self.interval_minutes,
            'total_intervals': len(consolidated['intervals']),
            'total_vehicles': consolidated['totals']['grand_total'],
            'peak_hour': peak_hour,
            'peak_interval': peak_interval,
            'vehicle_types': list(consolidated['totals']['by_class'].keys()),
            'counts_by_type': dict(consolidated['totals']['by_class'])
        }


def detect_video_sequence_times(video_files: List[str],
                                base_start_time: datetime) -> List[datetime]:
    """
    Detecta tiempos de inicio de una secuencia de videos
    
    Args:
        video_files: Lista de nombres de archivos de video
        base_start_time: Tiempo de inicio del primer video
        
    Returns:
        Lista de tiempos de inicio para cada video
    """
    # Esta función puede ser más sofisticada en el futuro
    # Por ahora asume que cada video tiene timestamps en el nombre
    # o usa duración estimada
    
    start_times = [base_start_time]
    
    # Por defecto asume 5 minutos por video
    default_duration = 5 * 60  # 5 minutos en segundos
    
    for i in range(1, len(video_files)):
        # Agregar duración del video anterior
        next_start = start_times[-1] + timedelta(seconds=default_duration)
        start_times.append(next_start)
    
    return start_times


if __name__ == "__main__":
    # Pruebas del consolidador
    print("=== Pruebas del Consolidator ===")
    
    # Crear consolidador
    consolidator = TrafficConsolidator(
        intersection_name="Av. República de Panamá con Vía Expresa",
        session_date=datetime(2024, 3, 15, 6, 0, 0),
        interval_minutes=15
    )
    
    # Simular 3 segmentos de video
    for i in range(3):
        start_time = datetime(2024, 3, 15, 6, 0, 0) + timedelta(minutes=i * 5)
        
        # Datos de prueba
        test_crossings = [
            {
                'timestamp': 30.0,
                'class_spanish': 'Auto',
                'direction': 'up_to_down',
                'track_id': f'track_{i}_1',
                'turn_number': 1
            }
        ]
        
        test_stats = {
            'elapsed_time': 300,
            'total_crossings': 1
        }
        
        consolidator.add_segment(
            video_name=f"video_segment_{i+1}.mp4",
            start_time=start_time,
            crossings=test_crossings,
            statistics=test_stats
        )
    
    # Obtener resumen
    summary = consolidator.get_summary()
    print(f"Intersección: {summary['intersection']}")
    print(f"Duración total: {summary['total_duration_hours']:.2f} horas")
    print(f"Total de segmentos: {summary['total_segments']}")
    print(f"Total de vehículos: {summary['total_vehicles']}")
    
    # Exportar a JSON
    consolidator.export_to_json("test_consolidation.json")
    
    print("\n✓ Módulo consolidator funcionando correctamente")
