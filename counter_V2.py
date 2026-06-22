import cv2
import numpy as np
from datetime import datetime, timedelta
from collections import defaultdict
import json

class CounterV2:
    """
    Sistema avanzado de conteo vehicular y peatonal.
    Soporta líneas, polígonos, giros prohibidos y consolidación temporal.
    """
    
    def __init__(self, lines=None, zones=None, interval_minutes=15):
        """
        Inicializa el contador.
        
        Args:
            lines: Lista de líneas de conteo
            zones: Lista de zonas poligonales
            interval_minutes: Intervalo de tiempo para agregación (default: 15 min)
        """
        self.lines = lines or []
        self.zones = zones or []
        self.interval_minutes = interval_minutes
        
        # Almacenamiento de conteos
        self.line_counts = defaultdict(lambda: defaultdict(lambda: defaultdict(int)))
        self.zone_counts = defaultdict(lambda: defaultdict(lambda: defaultdict(int)))
        
        # Tracking de objetos que ya cruzaron
        self.crossed_objects = defaultdict(set)  # {line_name: {track_id, ...}}
        self.zone_objects = defaultdict(set)     # {zone_name: {track_id, ...}}
        
        # Detección de giros prohibidos
        self.prohibited_turns = []
        self.violations = []
        
        # Timestamp de inicio
        self.start_time = None
        self.current_interval = None
        
        # Historial de trayectorias para análisis de giros
        self.trajectories = defaultdict(list)  # {track_id: [(x, y, timestamp), ...]}
    
    def set_start_time(self, timestamp):
        """Define el timestamp de inicio del video."""
        self.start_time = timestamp
        self.current_interval = self._get_interval(timestamp)
    
    def _get_interval(self, timestamp):
        """
        Calcula el intervalo de tiempo correspondiente.
        
        Args:
            timestamp: datetime object
            
        Returns:
            String con formato "HH:MM" del inicio del intervalo
        """
        if self.start_time is None:
            self.start_time = timestamp
        
        minutes = (timestamp - self.start_time).total_seconds() / 60
        interval_index = int(minutes // self.interval_minutes)
        
        interval_start = self.start_time + timedelta(minutes=interval_index * self.interval_minutes)
        return interval_start.strftime("%H:%M")
    
    def count(self, tracks, frame_timestamp=None):
        """
        Procesa los tracks y actualiza conteos.
        
        Args:
            tracks: Lista de tracks con formato:
                    [{'id': int, 'bbox': [x1,y1,x2,y2], 'class': str, 'centroid': (x,y)}]
            frame_timestamp: datetime del frame actual
            
        Returns:
            Dict con conteos actualizados
        """
        if frame_timestamp is None:
            frame_timestamp = datetime.now()
        
        if self.start_time is None:
            self.set_start_time(frame_timestamp)
        
        interval = self._get_interval(frame_timestamp)
        
        for track in tracks:
            track_id = track['id']
            centroid = track['centroid']
            vehicle_class = track['class']
            
            # Actualizar trayectoria
            self.trajectories[track_id].append((centroid[0], centroid[1], frame_timestamp))
            
            # Limitar historial de trayectoria (últimos 30 puntos)
            if len(self.trajectories[track_id]) > 30:
                self.trajectories[track_id].pop(0)
            
            # Procesar líneas de conteo
            self._process_lines(track_id, centroid, vehicle_class, interval)
            
            # Procesar zonas
            self._process_zones(track_id, centroid, vehicle_class, interval)
            
            # Detectar giros prohibidos
            self._detect_prohibited_turns(track_id, vehicle_class, frame_timestamp)
        
        return self.get_current_counts()
    
    def _process_lines(self, track_id, centroid, vehicle_class, interval):
        """Procesa el cruce de líneas."""
        for line in self.lines:
            line_name = line['name']
            direction = line['direction']
            p1, p2 = line['coords']
            
            # Verificar si el objeto ya cruzó esta línea
            if track_id in self.crossed_objects[line_name]:
                continue
            
            # Verificar cruce de línea
            if self._check_line_crossing(centroid, p1, p2):
                # Determinar dirección del cruce
                if self._verify_direction(track_id, p1, p2, direction):
                    self.line_counts[line_name][interval][vehicle_class] += 1
                    self.crossed_objects[line_name].add(track_id)
    
    def _process_zones(self, track_id, centroid, vehicle_class, interval):
        """Procesa la presencia en zonas."""
        for zone in self.zones:
            zone_name = zone['name']
            zone_type = zone['type']
            polygon = np.array(zone['coords'], np.int32)
            
            # Verificar si el centroide está dentro del polígono
            is_inside = cv2.pointPolygonTest(polygon, centroid, False) >= 0
            
            if zone_type == "Conteo":
                # Contar solo la primera vez que entra
                if is_inside and track_id not in self.zone_objects[zone_name]:
                    self.zone_counts[zone_name][interval][vehicle_class] += 1
                    self.zone_objects[zone_name].add(track_id)
            
            elif zone_type == "Exclusión":
                # Detectar violaciones (vehículos en zona prohibida)
                if is_inside:
                    self.violations.append({
                        'track_id': track_id,
                        'zone': zone_name,
                        'vehicle_class': vehicle_class,
                        'timestamp': interval
                    })
            
            elif zone_type == "Giro Prohibido":
                # Marcar para análisis posterior
                if is_inside:
                    self.zone_objects[zone_name].add(track_id)
    
    def _check_line_crossing(self, point, line_start, line_end):
        """
        Verifica si un punto está cerca de una línea.
        
        Args:
            point: (x, y) del centroide
            line_start: (x1, y1) inicio de línea
            line_end: (x2, y2) fin de línea
            
        Returns:
            True si el punto cruza la línea
        """
        # Calcular distancia del punto a la línea
        distance = self._point_to_line_distance(point, line_start, line_end)
        
        # Umbral de proximidad (píxeles)
        threshold = 15
        
        return distance < threshold
    
    def _point_to_line_distance(self, point, line_start, line_end):
        """Calcula la distancia perpendicular de un punto a una línea."""
        x0, y0 = point
        x1, y1 = line_start
        x2, y2 = line_end
        
        numerator = abs((y2 - y1) * x0 - (x2 - x1) * y0 + x2 * y1 - y2 * x1)
        denominator = np.sqrt((y2 - y1)**2 + (x2 - x1)**2)
        
        if denominator == 0:
            return float('inf')
        
        return numerator / denominator
    
    def _verify_direction(self, track_id, line_start, line_end, expected_direction):
        """
        Verifica si el objeto se mueve en la dirección esperada.
        
        Args:
            track_id: ID del track
            line_start: Punto inicial de la línea
            line_end: Punto final de la línea
            expected_direction: Dirección esperada (ej: "N-S")
            
        Returns:
            True si la dirección coincide
        """
        trajectory = self.trajectories.get(track_id, [])
        
        if len(trajectory) < 2:
            return True  # No hay suficiente información, aceptar por defecto
        
        # Obtener los últimos 2 puntos
        prev_point = trajectory[-2][:2]
        curr_point = trajectory[-1][:2]
        
        # Calcular vector de movimiento
        dx = curr_point[0] - prev_point[0]
        dy = curr_point[1] - prev_point[1]
        
        # Mapear dirección esperada a vector
        direction_map = {
            'N-S': (0, 1),   # Hacia abajo
            'S-N': (0, -1),  # Hacia arriba
            'E-O': (-1, 0),  # Hacia la izquierda
            'O-E': (1, 0),   # Hacia la derecha
            'NE-SO': (-1, 1),
            'NO-SE': (1, 1),
            'SE-NO': (-1, -1),
            'SO-NE': (1, -1)
        }
        
        expected_vector = direction_map.get(expected_direction, (0, 0))
        
        # Calcular producto punto (dot product)
        dot_product = dx * expected_vector[0] + dy * expected_vector[1]
        
        # Si el producto punto es positivo, la dirección es correcta
        return dot_product > 0
    
    def _detect_prohibited_turns(self, track_id, vehicle_class, timestamp):
        """Detecta giros prohibidos basándose en trayectorias."""
        # Implementación simplificada
        # En producción, esto analizaría la trayectoria completa
        # y compararía con zonas de "Giro Prohibido"
        pass
    
    def get_current_counts(self):
        """Retorna los conteos actuales."""
        return {
            'lines': dict(self.line_counts),
            'zones': dict(self.zone_counts),
            'violations': self.violations
        }
    
    def get_results(self):
        """
        Retorna resultados consolidados en formato estructurado.
        
        Returns:
            Dict con estructura completa de resultados
        """
        results = {
            'metadata': {
                'start_time': self.start_time.isoformat() if self.start_time else None,
                'interval_minutes': self.interval_minutes,
                'total_lines': len(self.lines),
                'total_zones': len(self.zones)
            },
            'line_counts': self._format_line_counts(),
            'zone_counts': self._format_zone_counts(),
            'violations': self.violations,
            'summary': self._calculate_summary()
        }
        
        return results
    
    def _format_line_counts(self):
        """Formatea conteos de líneas para exportación."""
        formatted = []
        
        for line_name, intervals in self.line_counts.items():
            line_data = {
                'name': line_name,
                'direction': self._get_line_direction(line_name),
                'intervals': []
            }
            
            for interval, counts in sorted(intervals.items()):
                interval_data = {
                    'time': interval,
                    'counts': dict(counts),
                    'total': sum(counts.values())
                }
                line_data['intervals'].append(interval_data)
            
            formatted.append(line_data)
        
        return formatted
    
    def _format_zone_counts(self):
        """Formatea conteos de zonas para exportación."""
        formatted = []
        
        for zone_name, intervals in self.zone_counts.items():
            zone_data = {
                'name': zone_name,
                'type': self._get_zone_type(zone_name),
                'intervals': []
            }
            
            for interval, counts in sorted(intervals.items()):
                interval_data = {
                    'time': interval,
                    'counts': dict(counts),
                    'total': sum(counts.values())
                }
                zone_data['intervals'].append(interval_data)
            
            formatted.append(zone_data)
        
        return formatted
    
    def _get_line_direction(self, line_name):
        """Obtiene la dirección de una línea por su nombre."""
        for line in self.lines:
            if line['name'] == line_name:
                return line['direction']
        return 'Unknown'
    
    def _get_zone_type(self, zone_name):
        """Obtiene el tipo de una zona por su nombre."""
        for zone in self.zones:
            if zone['name'] == zone_name:
                return zone['type']
        return 'Unknown'
    
    def _calculate_summary(self):
        """Calcula resumen estadístico."""
        total_vehicles = 0
        total_pedestrians = 0
        peak_hour = None
        peak_count = 0
        
        # Agregar conteos por hora
        hourly_counts = defaultdict(int)
        
        for line_name, intervals in self.line_counts.items():
            for interval, counts in intervals.items():
                hour = interval.split(':')[0]
                for vehicle_class, count in counts.items():
                    if vehicle_class == 'Peatón':
                        total_pedestrians += count
                    else:
                        total_vehicles += count
                        hourly_counts[hour] += count
        
        # Encontrar hora pico
        if hourly_counts:
            peak_hour = max(hourly_counts, key=hourly_counts.get)
            peak_count = hourly_counts[peak_hour]
        
        return {
            'total_vehicles': total_vehicles,
            'total_pedestrians': total_pedestrians,
            'peak_hour': peak_hour,
            'peak_count': peak_count,
            'total_violations': len(self.violations)
        }
    
    def export_to_json(self, filename):
        """Exporta resultados a JSON."""
        results = self.get_results()
        
        with open(filename, 'w') as f:
            json.dump(results, f, indent=4)
        
        return filename
    
    def reset(self):
        """Reinicia todos los contadores."""
        self.line_counts.clear()
        self.zone_counts.clear()
        self.crossed_objects.clear()
        self.zone_objects.clear()
        self.violations.clear()
        self.trajectories.clear()
        self.start_time = None