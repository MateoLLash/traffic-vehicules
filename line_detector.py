import cv2
import numpy as np
from sklearn.cluster import DBSCAN

class AutoLineDetector:
    """
    Detecta automáticamente líneas de conteo basándose en la estructura de la vía.
    Usa detección de bordes, transformada de Hough y clustering.
    """
    
    def __init__(self, frame):
        """
        Inicializa el detector.
        
        Args:
            frame: Frame de video (numpy array BGR)
        """
        self.frame = frame
        self.height, self.width = frame.shape[:2]
        self.gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    
    def detect_lanes(self, roi_mask=None):
        """
        Detecta carriles en la imagen.
        
        Args:
            roi_mask: Máscara opcional para limitar región de interés
            
        Returns:
            Lista de líneas detectadas con formato:
            [{'coords': [(x1,y1), (x2,y2)], 'angle': float, 'confidence': float}]
        """
        # Preprocesamiento
        blurred = cv2.GaussianBlur(self.gray, (5, 5), 0)
        
        # Detección de bordes
        edges = cv2.Canny(blurred, 50, 150, apertureSize=3)
        
        # Aplicar ROI si se proporciona
        if roi_mask is not None:
            edges = cv2.bitwise_and(edges, edges, mask=roi_mask)
        
        # Transformada de Hough para detectar líneas
        lines = cv2.HoughLinesP(
            edges,
            rho=1,
            theta=np.pi/180,
            threshold=50,
            minLineLength=100,
            maxLineGap=50
        )
        
        if lines is None:
            return []
        
        # Procesar y filtrar líneas
        detected_lines = []
        
        for line in lines:
            x1, y1, x2, y2 = line[0]
            
            # Calcular ángulo
            angle = np.arctan2(y2 - y1, x2 - x1) * 180 / np.pi
            
            # Calcular longitud
            length = np.sqrt((x2 - x1)**2 + (y2 - y1)**2)
            
            # Filtrar líneas muy cortas o muy horizontales/verticales
            if length < 50:
                continue
            
            # Calcular confianza basada en longitud
            confidence = min(length / 300, 1.0)
            
            detected_lines.append({
                'coords': [(x1, y1), (x2, y2)],
                'angle': angle,
                'length': length,
                'confidence': confidence
            })
        
        # Agrupar líneas similares
        clustered_lines = self._cluster_lines(detected_lines)
        
        return clustered_lines
    
    def _cluster_lines(self, lines):
        """
        Agrupa líneas similares usando clustering.
        
        Args:
            lines: Lista de líneas detectadas
            
        Returns:
            Lista de líneas representativas de cada cluster
        """
        if not lines:
            return []
        
        # Extraer características para clustering (ángulo y posición media)
        features = []
        for line in lines:
            x1, y1 = line['coords'][0]
            x2, y2 = line['coords'][1]
            mid_x = (x1 + x2) / 2
            mid_y = (y1 + y2) / 2
            angle = line['angle']
            
            features.append([mid_x / self.width, mid_y / self.height, angle / 180])
        
        features = np.array(features)
        
        # Clustering DBSCAN
        clustering = DBSCAN(eps=0.1, min_samples=2).fit(features)
        labels = clustering.labels_
        
        # Obtener línea representativa de cada cluster
        clustered_lines = []
        unique_labels = set(labels)
        
        for label in unique_labels:
            if label == -1:  # Ruido
                continue
            
            # Obtener líneas del cluster
            cluster_lines = [lines[i] for i in range(len(lines)) if labels[i] == label]
            
            # Seleccionar la línea más larga como representativa
            representative = max(cluster_lines, key=lambda x: x['length'])
            clustered_lines.append(representative)
        
        return clustered_lines
    
    def suggest_counting_lines(self, num_suggestions=4):
        """
        Sugiere líneas de conteo óptimas.
        
        Args:
            num_suggestions: Número de líneas a sugerir
            
        Returns:
            Lista de líneas sugeridas con direcciones inferidas
        """
        # Detectar carriles
        detected_lines = self.detect_lanes()
        
        if not detected_lines:
            # Si no se detectan líneas, sugerir líneas por defecto
            return self._default_suggestions()
        
        # Ordenar por confianza
        detected_lines.sort(key=lambda x: x['confidence'], reverse=True)
        
        # Tomar las mejores líneas
        suggestions = []
        
        for idx, line in enumerate(detected_lines[:num_suggestions]):
            # Inferir dirección basada en ángulo
            direction = self._infer_direction(line['angle'])
            
            # Extender línea para que cruce toda la vía
            extended_coords = self._extend_line(line['coords'])
            
            suggestions.append({
                'name': f'Línea_Sugerida_{idx + 1}',
                'direction': direction,
                'coords': extended_coords,
                'color': self._get_color_for_direction(direction),
                'stroke_width': 4,
                'confidence': line['confidence'],
                'auto_detected': True
            })
        
        return suggestions
    
    def _infer_direction(self, angle):
        """
        Infiere la dirección del flujo basándose en el ángulo de la línea.
        
        Args:
            angle: Ángulo en grados
            
        Returns:
            String con dirección (ej: "N-S")
        """
        # Normalizar ángulo a [0, 360)
        angle = angle % 360
        
        # Mapear ángulo a dirección
        if 337.5 <= angle or angle < 22.5:
            return 'O-E'
        elif 22.5 <= angle < 67.5:
            return 'SO-NE'
        elif 67.5 <= angle < 112.5:
            return 'S-N'
        elif 112.5 <= angle < 157.5:
            return 'SE-NO'
        elif 157.5 <= angle < 202.5:
            return 'E-O'
        elif 202.5 <= angle < 247.5:
            return 'NE-SO'
        elif 247.5 <= angle < 292.5:
            return 'N-S'
        else:  # 292.5 <= angle < 337.5
            return 'NO-SE'
    
    def _extend_line(self, coords):
        """
        Extiende una línea para que cruce todo el frame.
        
        Args:
            coords: [(x1, y1), (x2, y2)]
            
        Returns:
            Coordenadas extendidas
        """
        (x1, y1), (x2, y2) = coords
        
        # Calcular pendiente
        if x2 - x1 == 0:
            # Línea vertical
            return [(x1, 0), (x1, self.height)]
        
        m = (y2 - y1) / (x2 - x1)
        b = y1 - m * x1
        
        # Calcular intersecciones con los bordes del frame
        intersections = []
        
        # Borde izquierdo (x=0)
        y = b
        if 0 <= y <= self.height:
            intersections.append((0, int(y)))
        
        # Borde derecho (x=width)
        y = m * self.width + b
        if 0 <= y <= self.height:
            intersections.append((self.width, int(y)))
        
        # Borde superior (y=0)
        if m != 0:
            x = -b / m
            if 0 <= x <= self.width:
                intersections.append((int(x), 0))
        
        # Borde inferior (y=height)
        if m != 0:
            x = (self.height - b) / m
            if 0 <= x <= self.width:
                intersections.append((int(x), self.height))
        
        # Retornar los dos puntos más alejados
        if len(intersections) >= 2:
            return [intersections[0], intersections[-1]]
        
        return coords
    
    def _get_color_for_direction(self, direction):
        """Asigna un color basado en la dirección."""
        color_map = {
            'N-S': '#00FF00',
            'S-N': '#00FFFF',
            'E-O': '#FF00FF',
            'O-E': '#FFFF00',
            'NE-SO': '#FF8800',
            'NO-SE': '#8800FF',
            'SE-NO': '#00FF88',
            'SO-NE': '#FF0088'
        }
        return color_map.get(direction, '#FFFFFF')
    
    def _default_suggestions(self):
        """Retorna sugerencias por defecto si no se detectan líneas."""
        # Líneas horizontales y verticales en el centro
        center_x = self.width // 2
        center_y = self.height // 2
        
        return [
            {
                'name': 'Línea_Horizontal_1',
                'direction': 'O-E',
                'coords': [(0, center_y - 100), (self.width, center_y - 100)],
                'color': '#00FF00',
                'stroke_width': 4,
                'confidence': 0.5,
                'auto_detected': False
            },
            {
                'name': 'Línea_Horizontal_2',
                'direction': 'E-O',
                'coords': [(0, center_y + 100), (self.width, center_y + 100)],
                'color': '#00FFFF',
                'stroke_width': 4,
                'confidence': 0.5,
                'auto_detected': False
            },
            {
                'name': 'Línea_Vertical_1',
                'direction': 'N-S',
                'coords': [(center_x - 100, 0), (center_x - 100, self.height)],
                'color': '#FF00FF',
                'stroke_width': 4,
                'confidence': 0.5,
                'auto_detected': False
            },
            {
                'name': 'Línea_Vertical_2',
                'direction': 'S-N',
                'coords': [(center_x + 100, 0), (center_x + 100, self.height)],
                'color': '#FFFF00',
                'stroke_width': 4,
                'confidence': 0.5,
                'auto_detected': False
            }
        ]
    
    def visualize_detection(self, lines):
        """
        Visualiza las líneas detectadas sobre el frame.
        
        Args:
            lines: Lista de líneas a visualizar
            
        Returns:
            Frame con líneas dibujadas
        """
        vis_frame = self.frame.copy()
        
        for line in lines:
            coords = line['coords']
            color_hex = line.get('color', '#00FF00')
            
            # Convertir color hex a BGR
            color_hex = color_hex.lstrip('#')
            rgb = tuple(int(color_hex[i:i+2], 16) for i in (0, 2, 4))
            bgr = (rgb[2], rgb[1], rgb[0])
            
            # Dibujar línea
            cv2.line(vis_frame, coords[0], coords[1], bgr, line.get('stroke_width', 4))
            
            # Etiqueta
            mid_point = (
                (coords[0][0] + coords[1][0]) // 2,
                (coords[0][1] + coords[1][1]) // 2
            )
            
            label = f"{line['name']} ({line['direction']})"
            if 'confidence' in line:
                label += f" [{line['confidence']:.0%}]"
            
            cv2.putText(vis_frame, label, mid_point,
                       cv2.FONT_HERSHEY_SIMPLEX, 0.6, bgr, 2)
        
        return vis_frame