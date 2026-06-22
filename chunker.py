"""
chunker.py - Módulo para procesar videos largos por segmentos

Parte videos en chunks de N minutos usando ffmpeg (sin recodificar = rápido).
Cada chunk se borra del disco inmediatamente después de procesarse.

Uso desde app.py:
    from chunker import VideoChunker
"""

import os
import subprocess
import shutil
import cv2
from pathlib import Path
from datetime import timedelta


# ─────────────────────────────────────────────
# VERIFICACIÓN DE FFMPEG
# ─────────────────────────────────────────────

def ffmpeg_available() -> bool:
    """Verifica si ffmpeg está instalado en el sistema."""
    return shutil.which("ffmpeg") is not None


def ffmpeg_install_instructions() -> str:
    """Instrucciones de instalación según el OS."""
    import platform
    os_name = platform.system()
    if os_name == "Windows":
        return (
            "ffmpeg no está instalado.\n\n"
            "Instálalo con:\n"
            "  winget install ffmpeg\n\n"
            "O descárgalo de: https://ffmpeg.org/download.html\n"
            "y agrega la carpeta bin/ al PATH del sistema."
        )
    elif os_name == "Darwin":
        return "ffmpeg no instalado. Corre: brew install ffmpeg"
    else:
        return "ffmpeg no instalado. Corre: sudo apt install ffmpeg"


# ─────────────────────────────────────────────
# UTILIDADES DE VIDEO
# ─────────────────────────────────────────────

def get_video_info(video_path: str) -> dict:
    """
    Retorna información completa del video.
    Returns:
        {duration_s, duration_h, fps, width, height, frame_count, size_mb}
    """
    cap = cv2.VideoCapture(video_path)
    fps         = cap.get(cv2.CAP_PROP_FPS) or 30
    frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    width       = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height      = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    cap.release()

    duration_s = frame_count / fps
    size_mb    = os.path.getsize(video_path) / (1024 * 1024)

    return {
        "duration_s":   duration_s,
        "duration_h":   duration_s / 3600,
        "duration_min": duration_s / 60,
        "fps":          fps,
        "width":        width,
        "height":       height,
        "frame_count":  frame_count,
        "size_mb":      size_mb,
    }


def format_duration(seconds: float) -> str:
    """Convierte segundos a string legible: '2h 15min' o '45min'."""
    h   = int(seconds // 3600)
    m   = int((seconds % 3600) // 60)
    s   = int(seconds % 60)
    if h > 0:
        return f"{h}h {m:02d}min"
    elif m > 0:
        return f"{m}min {s:02d}s"
    else:
        return f"{s}s"


def needs_chunking(video_path: str, threshold_minutes: int = 30) -> bool:
    """Retorna True si el video supera el umbral de duración."""
    info = get_video_info(video_path)
    return info["duration_min"] > threshold_minutes


# ─────────────────────────────────────────────
# CLASE PRINCIPAL
# ─────────────────────────────────────────────

class VideoChunker:
    """
    Gestiona la división y procesamiento de videos largos por chunks.

    Ejemplo de uso:
        chunker = VideoChunker(video_path, chunk_minutes=15, output_dir="temp/chunks")
        chunks  = chunker.split()           # genera los archivos
        info    = chunker.get_chunk_info()  # lista de dicts con metadata

        for i, chunk_path in enumerate(chunks):
            procesar(chunk_path)
            chunker.delete_chunk(chunk_path)  # libera disco inmediatamente
    """

    def __init__(self,
                 video_path:    str,
                 chunk_minutes: int = 15,
                 output_dir:    str = "temp/chunks"):
        self.video_path    = video_path
        self.chunk_minutes = chunk_minutes
        self.chunk_seconds = chunk_minutes * 60
        self.output_dir    = output_dir
        self.video_info    = get_video_info(video_path)
        self._chunks:      list[str] = []

    # ── propiedades ───────────────────────────

    @property
    def total_chunks(self) -> int:
        import math
        return max(1, math.ceil(
            self.video_info["duration_s"] / self.chunk_seconds
        ))

    @property
    def total_duration_str(self) -> str:
        return format_duration(self.video_info["duration_s"])

    def chunk_timestamp(self, chunk_index: int) -> timedelta:
        """Retorna el timedelta de inicio de un chunk (para timestamps del Excel)."""
        return timedelta(seconds=chunk_index * self.chunk_seconds)

    def chunk_label(self, chunk_index: int) -> str:
        """Retorna etiqueta legible: 'Chunk 3/32 · 00:30–00:45'."""
        start_s = chunk_index * self.chunk_seconds
        end_s   = min(start_s + self.chunk_seconds,
                      self.video_info["duration_s"])
        start_str = format_duration(start_s)
        end_str   = format_duration(end_s)
        return f"Chunk {chunk_index+1}/{self.total_chunks} · {start_str}–{end_str}"

    # ── operaciones ───────────────────────────

    def split(self) -> list[str]:
        """
        Parte el video en chunks usando ffmpeg -c copy (sin recodificar).
        Retorna lista ordenada de rutas a los chunks generados.
        Lanza RuntimeError si ffmpeg no está disponible.
        """
        if not ffmpeg_available():
            raise RuntimeError(ffmpeg_install_instructions())

        os.makedirs(self.output_dir, exist_ok=True)

        # Limpiar chunks anteriores si existen
        for f in Path(self.output_dir).glob("chunk_*.mp4"):
            f.unlink()

        output_pattern = os.path.join(self.output_dir, "chunk_%03d.mp4")

        cmd = [
            "ffmpeg",
            "-i", self.video_path,
            "-c", "copy",              # sin recodificar — muy rápido
            "-map", "0",
            "-segment_time", str(self.chunk_seconds),
            "-f", "segment",
            "-reset_timestamps", "1",
            "-avoid_negative_ts", "1",
            "-y",                      # sobreescribir sin preguntar
            output_pattern
        ]

        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True
        )

        if result.returncode != 0:
            raise RuntimeError(
                f"ffmpeg falló al partir el video:\n{result.stderr[-500:]}"
            )

        self._chunks = sorted([
            str(p) for p in Path(self.output_dir).glob("chunk_*.mp4")
        ])
        return self._chunks

    def delete_chunk(self, chunk_path: str) -> None:
        """Borra un chunk del disco para liberar espacio."""
        try:
            if os.path.exists(chunk_path):
                os.remove(chunk_path)
        except Exception:
            pass  # no crítico

    def cleanup(self) -> None:
        """Borra todos los chunks y el directorio temporal."""
        try:
            shutil.rmtree(self.output_dir, ignore_errors=True)
        except Exception:
            pass

    def get_chunk_info(self) -> list[dict]:
        """
        Retorna lista de dicts con metadata de cada chunk esperado.
        Útil para mostrar el plan de procesamiento antes de empezar.
        """
        info = []
        for i in range(self.total_chunks):
            start_s = i * self.chunk_seconds
            end_s   = min(start_s + self.chunk_seconds,
                          self.video_info["duration_s"])
            info.append({
                "index":     i,
                "label":     self.chunk_label(i),
                "start_s":   start_s,
                "end_s":     end_s,
                "start_str": format_duration(start_s),
                "end_str":   format_duration(end_s),
                "duration_s": end_s - start_s,
            })
        return info


# ─────────────────────────────────────────────
# CONSOLIDADOR DE ESTADÍSTICAS
# ─────────────────────────────────────────────

def consolidate_stats(stats_list: list[dict]) -> dict:
    """
    Combina las estadísticas de múltiples chunks en un resultado final único.
    El resultado tiene exactamente la misma estructura que el stats de un
    video completo — la capa de resultados/exportación no nota diferencia.

    Args:
        stats_list: Lista de dicts retornados por counter.get_statistics()
                    uno por cada chunk procesado.
    Returns:
        dict con la misma estructura que stats individual.
    """
    if not stats_list:
        return {}
    if len(stats_list) == 1:
        return stats_list[0]

    # Totales globales
    total_crossings   = sum(s.get("total_crossings", 0)   for s in stats_list)
    elapsed_minutes   = sum(s.get("elapsed_minutes", 0)   for s in stats_list)
    total_lines       = stats_list[0].get("total_lines",  0)  # mismo en todos

    # Sumar conteos totales por clase
    total_counts: dict[str, int] = {}
    for s in stats_list:
        for cls, cnt in s.get("total_counts", {}).items():
            total_counts[cls] = total_counts.get(cls, 0) + cnt

    # Consolidar counts_by_line
    # Estructura: lista de {line_name, total_count, counts_by_class}
    lines_merged: dict[str, dict] = {}

    for s in stats_list:
        for line_info in s.get("counts_by_line", []):
            lname = line_info["line_name"]
            if lname not in lines_merged:
                lines_merged[lname] = {
                    "line_name":      lname,
                    "total_count":    0,
                    "counts_by_class": {}
                }
            lines_merged[lname]["total_count"] += line_info.get("total_count", 0)

            for cls, dirs in line_info.get("counts_by_class", {}).items():
                if cls not in lines_merged[lname]["counts_by_class"]:
                    lines_merged[lname]["counts_by_class"][cls] = {
                        "total": 0,
                        "up_to_down": 0, "down_to_up": 0,
                        "left_to_right": 0, "right_to_left": 0
                    }
                for direction in ["total", "up_to_down", "down_to_up",
                                  "left_to_right", "right_to_left"]:
                    lines_merged[lname]["counts_by_class"][cls][direction] += \
                        dirs.get(direction, 0)

    return {
        "total_crossings":  total_crossings,
        "total_lines":      total_lines,
        "elapsed_minutes":  elapsed_minutes,
        "total_counts":     total_counts,
        "counts_by_line":   list(lines_merged.values()),
    }


def consolidate_crossings(crossings_list: list[list]) -> list:
    """
    Concatena todos los eventos de cruce de todos los chunks.
    Los timestamps ya vienen ajustados desde process_video.
    """
    result = []
    for crossings in crossings_list:
        result.extend(crossings)
    return result