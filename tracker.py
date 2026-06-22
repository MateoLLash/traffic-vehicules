"""
tracker.py - Módulo de tracking de objetos

Cambios v2:
1. max_age=30        → recuerda vehículos tapados por más tiempo
2. Voting de clase   → usa la clase más frecuente en los últimos 10 frames
3. Sin restricción de clase en asociación → tracks sobreviven si cambia la clase detectada
"""

import numpy as np
from typing import List, Dict, Tuple, Optional
from collections import defaultdict, deque
from scipy.optimize import linear_sum_assignment
from scipy.spatial.distance import euclidean

from utils import setup_logger, calculate_centroid, OBJECT_CLASSES

logger = setup_logger('tracker')


class Track:
    """
    Representa un objeto rastreado a lo largo del tiempo.
    
    Cambio v2: agrega class_history para voting de clase.
    """
    
    def __init__(self, track_id: int, detection: Dict, frame_number: int):
        self.track_id = track_id

        # ── VOTING: historial de las últimas 10 clases detectadas ──────────
        self.class_history = deque(maxlen=10)
        self.class_history.append(detection['class_name'])
        # La clase y el nombre en español se calculan por voting
        self.class_name    = detection['class_name']
        self.class_spanish = detection['class_spanish']
        # ───────────────────────────────────────────────────────────────────

        # Historial de posiciones
        self.bboxes      = deque(maxlen=30)
        self.centroids   = deque(maxlen=30)
        self.confidences = deque(maxlen=30)
        self.frames      = deque(maxlen=30)

        self.bboxes.append(detection['bbox'])
        self.centroids.append(detection['centroid'])
        self.confidences.append(detection['confidence'])
        self.frames.append(frame_number)

        self.age               = 0
        self.time_since_update = 0
        self.hits              = 1
        self.state             = 'active'
        self.velocity          = (0, 0)

    # ── VOTING: actualiza clase usando la más frecuente ────────────────────
    def _update_class_by_voting(self):
        """
        Elige la clase más frecuente en los últimos 10 frames.
        Evita que un frame ruidoso cambie la clase del track.
        
        Ejemplo:
          historial = [auto, auto, camioneta, auto, auto]
          → voting: auto=4, camioneta=1 → clase = "auto"
        """
        if not self.class_history:
            return
        voted_class = max(set(self.class_history),
                          key=self.class_history.count)
        self.class_name    = voted_class
        # Actualizar nombre en español desde OBJECT_CLASSES
        self.class_spanish = OBJECT_CLASSES.get(
            voted_class, {}
        ).get('name', voted_class)
    # ───────────────────────────────────────────────────────────────────────

    def update(self, detection: Dict, frame_number: int):
        """Actualiza el track con una nueva detección."""
        self.bboxes.append(detection['bbox'])
        self.centroids.append(detection['centroid'])
        self.confidences.append(detection['confidence'])
        self.frames.append(frame_number)

        # Agregar clase al historial y recalcular por voting
        self.class_history.append(detection['class_name'])
        self._update_class_by_voting()

        self.time_since_update = 0
        self.hits += 1
        self.state = 'active'

        if len(self.centroids) >= 2:
            prev = self.centroids[-2]
            curr = self.centroids[-1]
            self.velocity = (curr[0] - prev[0], curr[1] - prev[1])

    def predict(self) -> Tuple[int, int, int, int]:
        """Predice la siguiente posición."""
        if not self.bboxes:
            return (0, 0, 0, 0)
        last_bbox = self.bboxes[-1]
        if len(self.centroids) >= 2:
            vx, vy = self.velocity
            x1, y1, x2, y2 = last_bbox
            w, h = x2 - x1, y2 - y1
            return (int(x1+vx), int(y1+vy),
                    int(x1+vx+w), int(y1+vy+h))
        return last_bbox

    def mark_missed(self):
        """Marca el track como no actualizado en este frame."""
        self.time_since_update += 1
        self.age += 1
        if self.time_since_update > 5:
            self.state = 'lost'

    def get_current_bbox(self):
        return self.bboxes[-1] if self.bboxes else (0,0,0,0)

    def get_current_centroid(self):
        return self.centroids[-1] if self.centroids else (0,0)

    def get_trajectory(self):
        return list(self.centroids)

    def get_average_confidence(self):
        return float(np.mean(self.confidences)) if self.confidences else 0.0

    def to_dict(self):
        return {
            'track_id':    self.track_id,
            'class_name':  self.class_name,
            'class_spanish': self.class_spanish,
            'bbox':        self.get_current_bbox(),
            'centroid':    self.get_current_centroid(),
            'confidence':  self.get_average_confidence(),
            'trajectory':  self.get_trajectory(),
            'hits':        self.hits,
            'age':         self.age,
            'state':       self.state,
        }


class ObjectTracker:
    """
    Tracker multi-objeto basado en IoU + distancia de centroides.
    
    Cambios v2:
    - max_age=30 por defecto (antes 10) → menos IDs perdidos al taparse
    - Asociación sin restricción de clase → el track sobrevive aunque
      el modelo cambie de opinión en un frame, el voting corrige la clase
    """

    def __init__(self,
                 max_age: int = 30,          # ← era 10, ahora 30
                 min_hits: int = 3,
                 iou_threshold: float = 0.3,
                 distance_threshold: float = 80):  # ← era 50, ahora 80
        self.tracks             = {}
        self.next_id            = 1
        self.max_age            = max_age
        self.min_hits           = min_hits
        self.iou_threshold      = iou_threshold
        self.distance_threshold = distance_threshold
        self.total_tracks_created = 0
        self.finished_tracks    = []
        logger.info(f"Tracker v2: max_age={max_age}, min_hits={min_hits}, "
                    f"distance_threshold={distance_threshold}")

    def update(self, detections: List[Dict], frame_number: int) -> List[Track]:
        for track in self.tracks.values():
            track.age += 1

        if not detections:
            for track in self.tracks.values():
                track.mark_missed()
            return self._get_active_tracks()

        if not self.tracks:
            for det in detections:
                self._create_track(det, frame_number)
            return self._get_active_tracks()

        matched, unmatched_dets, unmatched_tracks = \
            self._associate_detections_to_tracks(
                detections, list(self.tracks.values())
            )

        for det_idx, track_id in matched:
            self.tracks[track_id].update(detections[det_idx], frame_number)

        for det_idx in unmatched_dets:
            self._create_track(detections[det_idx], frame_number)

        for track_id in unmatched_tracks:
            if track_id in self.tracks:
                self.tracks[track_id].mark_missed()

        self._remove_dead_tracks()
        return self._get_active_tracks()

    def _create_track(self, detection: Dict, frame_number: int) -> Track:
        track = Track(self.next_id, detection, frame_number)
        self.tracks[self.next_id] = track
        self.next_id += 1
        self.total_tracks_created += 1
        return track

    def _associate_detections_to_tracks(self,
                                        detections, tracks):
        if not tracks:
            return [], list(range(len(detections))), []
        if not detections:
            return [], [], [t.track_id for t in tracks]

        cost_matrix = np.zeros((len(detections), len(tracks)))

        for d, det in enumerate(detections):
            det_bbox     = det['bbox']
            det_centroid = det['centroid']

            for t, track in enumerate(tracks):
                track_bbox     = track.get_current_bbox()
                track_centroid = track.get_current_centroid()

                # ── Sin penalización por clase diferente ────────────────
                # El voting en Track.update() corregirá la clase.
                # Penalizar aquí causaba que tracks perdieran su ID
                # cuando el modelo cambiaba de opinión un frame.
                # ────────────────────────────────────────────────────────

                iou  = self._calculate_iou(det_bbox, track_bbox)
                dist = euclidean(det_centroid, track_centroid)
                normalized_dist = dist / self.distance_threshold

                # Pequeño bonus si la clase coincide (sin bloqueo total)
                class_penalty = 0.0 if det['class_name'] == track.class_name \
                                else 0.2

                cost_matrix[d, t] = (1 - iou) + normalized_dist + class_penalty

        det_indices, track_indices = linear_sum_assignment(cost_matrix)

        matched         = []
        unmatched_dets  = list(range(len(detections)))
        unmatched_tracks = [t.track_id for t in tracks]

        for d, t in zip(det_indices, track_indices):
            det_bbox     = detections[d]['bbox']
            track_bbox   = tracks[t].get_current_bbox()
            iou          = self._calculate_iou(det_bbox, track_bbox)
            det_centroid = detections[d]['centroid']
            track_centroid = tracks[t].get_current_centroid()
            dist         = euclidean(det_centroid, track_centroid)

            if iou >= self.iou_threshold or dist <= self.distance_threshold:
                matched.append((d, tracks[t].track_id))
                if d in unmatched_dets:
                    unmatched_dets.remove(d)
                if tracks[t].track_id in unmatched_tracks:
                    unmatched_tracks.remove(tracks[t].track_id)

        return matched, unmatched_dets, unmatched_tracks

    def _calculate_iou(self, bbox1, bbox2) -> float:
        x1_1, y1_1, x2_1, y2_1 = bbox1
        x1_2, y1_2, x2_2, y2_2 = bbox2
        x1_i = max(x1_1, x1_2); y1_i = max(y1_1, y1_2)
        x2_i = min(x2_1, x2_2); y2_i = min(y2_1, y2_2)
        if x2_i < x1_i or y2_i < y1_i:
            return 0.0
        intersection = (x2_i - x1_i) * (y2_i - y1_i)
        area1  = (x2_1 - x1_1) * (y2_1 - y1_1)
        area2  = (x2_2 - x1_2) * (y2_2 - y1_2)
        union  = area1 + area2 - intersection
        return 0.0 if union == 0 else intersection / union

    def _get_active_tracks(self):
        return [t for t in self.tracks.values() if t.state == 'active']

    def _remove_dead_tracks(self):
        dead = [tid for tid, t in self.tracks.items()
                if t.time_since_update > self.max_age]
        for tid in dead:
            self.tracks[tid].state = 'finished'
            self.finished_tracks.append(self.tracks[tid])
            del self.tracks[tid]

    def get_valid_tracks(self):
        return [t for t in self.tracks.values()
                if t.hits >= self.min_hits and t.state == 'active']

    def get_track_by_id(self, track_id):
        return self.tracks.get(track_id)

    def get_all_tracks(self):
        return list(self.tracks.values())

    def get_statistics(self):
        return {
            'total_tracks_created': self.total_tracks_created,
            'active_tracks':  len(self._get_active_tracks()),
            'valid_tracks':   len(self.get_valid_tracks()),
            'finished_tracks': len(self.finished_tracks),
            'lost_tracks':    len([t for t in self.tracks.values()
                                   if t.state == 'lost']),
        }

    def reset(self):
        self.tracks = {}
        self.next_id = 1
        self.finished_tracks = []
        self.total_tracks_created = 0
        logger.info("Tracker reseteado")


# Compatibilidad: alias moderno esperado por algunas partes de la app
Tracker = ObjectTracker


if __name__ == "__main__":
    print("=== Pruebas del Tracker v2 ===")
    tracker = ObjectTracker()
    detections = [{
        'bbox': (100,100,200,200), 'centroid': (150,150),
        'confidence': 0.9, 'class_name': 'auto', 'class_spanish': 'Auto'
    }]
    tracks = tracker.update(detections, 1)
    print(f"Frame 1: {len(tracks)} tracks")
    print(f"Stats: {tracker.get_statistics()}")
    print("✓ Tracker v2 funcionando")