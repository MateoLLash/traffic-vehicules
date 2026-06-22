"""
app.py - Aplicación Streamlit para análisis de tráfico vehicular y peatonal
"""

import streamlit as st
import cv2
import numpy as np
import time
import tempfile
import os
import streamlit.components.v1 as components
from pathlib import Path
from datetime import datetime, timedelta
import pandas as pd
from PIL import Image

from detector import ObjectDetector, create_detector
from tracker import ObjectTracker
from counter import TrafficCounter, CountingLine
from exporter import DataExporter
from excel_aforo_mtc import ExcelAforoMTC
from visualizer import TrafficVisualizer
from utils import (setup_logger, create_output_dirs, get_video_properties,
                   validate_video_file, estimate_processing_time, OBJECT_CLASSES)

from theme import (apply_theme, header, section_title, sidebar_label,
                   status_badge, metric_card, video_info_card,
                   step_indicator, live_metrics_panel)
from components import video_player, sidebar_brand, empty_state
from chunker import (VideoChunker, consolidate_stats, consolidate_crossings,
                     get_video_info, needs_chunking, ffmpeg_available,
                     format_duration)
from drawing_tool import DrawingTool

st.set_page_config(
    page_title="Traffic Analysis Tool · Lima",
    page_icon="🚦",
    layout="wide",
    initial_sidebar_state="expanded"
)

apply_theme()
logger = setup_logger('app', 'logs/app.log')


# ==================== ESTADO DE LA SESIÓN ====================

if 'initialized' not in st.session_state:
    st.session_state.initialized = True
    st.session_state.video_uploaded = False
    st.session_state.video_path = None
    st.session_state.video_properties = None
    st.session_state.detector = None
    st.session_state.tracker = None
    st.session_state.counter = None
    st.session_state.counting_lines = []
    st.session_state.processing_complete = False
    st.session_state.statistics = None
    st.session_state.crossings = []
    st.session_state.time_series = None
    st.session_state.output_dirs = None
    st.session_state.frame_for_lines = None
    st.session_state.canvas_scale_factor = 1.0
    st.session_state.processed_video_path = None
    st.session_state.lines_panel_collapsed = False


# ==================== FUNCIONES AUXILIARES ====================

def load_video(video_file):
    try:
        temp_dir = tempfile.mkdtemp()
        video_path = os.path.join(temp_dir, video_file.name)
        with open(video_path, 'wb') as f:
            f.write(video_file.read())
        if not validate_video_file(video_path):
            st.error("El archivo no es un video válido.")
            return None
        properties = get_video_properties(video_path)
        return video_path, properties
    except Exception as e:
        st.error(f"Error al cargar video: {e}")
        logger.error(f"Error al cargar video: {e}")
        return None


def get_first_frame(video_path):
    cap = cv2.VideoCapture(video_path)
    ret, frame = cap.read()
    cap.release()
    if ret:
        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        return np.ascontiguousarray(rgb, dtype=np.uint8)
    return None


def resize_frame_for_canvas(frame, max_width=1000):
    h, w = frame.shape[:2]
    if w <= max_width:
        return frame, 1.0
    scale = w / max_width
    new_w = max_width
    new_h = int(h / scale)
    resized = cv2.resize(frame, (new_w, new_h), interpolation=cv2.INTER_LINEAR)
    return resized, scale


def draw_line_on_frame(frame_rgb, lines):
    bgr = cv2.cvtColor(np.ascontiguousarray(frame_rgb, dtype=np.uint8), cv2.COLOR_RGB2BGR)
    for line in lines:
        cv2.line(bgr, line['start'], line['end'], line['color'], 3)
        mid_x = (line['start'][0] + line['end'][0]) // 2
        mid_y = (line['start'][1] + line['end'][1]) // 2
        cv2.putText(bgr, line['name'], (mid_x, mid_y),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.7, line['color'], 2)
    return np.ascontiguousarray(cv2.cvtColor(bgr, cv2.COLOR_BGR2RGB), dtype=np.uint8)


def _step_actual():
    if st.session_state.processing_complete:
        return 3
    if len(st.session_state.counting_lines) > 0:
        return 2
    if st.session_state.detector is not None:
        return 1
    if st.session_state.video_uploaded:
        return 1
    return 0


def opencv_gui_available():
    try:
        cv2.namedWindow("_test_opencv_gui_", cv2.WINDOW_NORMAL)
        cv2.destroyWindow("_test_opencv_gui_")
        return True
    except Exception:
        return False


def process_video(video_path, detector, tracker, counter,
                  save_video=False, show_visualizations=True,
                  use_opencv_window=False):
    try:
        cap = cv2.VideoCapture(video_path)
        fps = cap.get(cv2.CAP_PROP_FPS)
        width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        frame_skip = 2

        output_video_path = None
        if save_video:
            output_dirs = st.session_state.output_dirs
            output_video_path = os.path.join(
                output_dirs['videos'],
                f"processed_{datetime.now().strftime('%Y%m%d_%H%M%S')}.mp4"
            )
            fourcc = cv2.VideoWriter_fourcc(*'mp4v')
            out = cv2.VideoWriter(output_video_path, fourcc, fps, (width, height))

        if show_visualizations:
            progress_bar = st.progress(0)
            status_text = st.empty()
            metrics_slot = st.empty()
            video_placeholder = st.empty()
            stats_placeholder = st.empty()

        frame_count = 0
        all_crossings = []
        proc_start = time.time()

        class FlickerAnalyzer:
            def __init__(self):
                self.history = {}
                self.flicker_count = {}

            def log(self, track_id, class_name):
                if track_id not in self.history:
                    self.history[track_id] = []
                history = self.history[track_id]
                if history and history[-1] != class_name:
                    self.flicker_count[track_id] = self.flicker_count.get(track_id, 0) + 1
                history.append(class_name)

            def report(self):
                print("\n=== Clases con más flickering ===")
                for track_id, count in sorted(self.flicker_count.items(),
                                              key=lambda x: x[1], reverse=True)[:10]:
                    unique = set(self.history[track_id])
                    print(f"Track {track_id}: {count} cambios entre {unique}")

        flicker_analyzer = FlickerAnalyzer()

        while True:
            ret, frame = cap.read()
            if not ret:
                break

            frame_count += 1
            if frame_count % frame_skip != 0:
                continue

            detections = detector.detect(frame)
            for det in detections:
                tid = det.get('track_id', -1)
                if tid != -1:
                    flicker_analyzer.log(tid, det['class_name'])

            tracks = tracker.update(detections, frame_count)
            valid_tracks = tracker.get_valid_tracks()
            crossings = counter.update(valid_tracks, frame_count)
            all_crossings.extend(crossings)

            if save_video or show_visualizations:
                frame_vis = frame.copy()
                for track in valid_tracks:
                    bbox = track.get_current_bbox()
                    color = OBJECT_CLASSES.get(track.class_name, {}).get('color', (200, 200, 200))
                    x1, y1, x2, y2 = bbox
                    cv2.rectangle(frame_vis, (x1, y1), (x2, y2), color, 2)
                    label = f"{track.class_spanish} #{track.track_id}"
                    font = cv2.FONT_HERSHEY_SIMPLEX
                    font_scale = 0.45
                    thickness = 1
                    (tw, th), _ = cv2.getTextSize(label, font, font_scale, thickness)
                    cv2.rectangle(frame_vis, (x1, y1 - th - 8), (x1 + tw + 6, y1), color, -1)
                    cv2.putText(frame_vis, label, (x1 + 3, y1 - 4),
                                font, font_scale, (0, 0, 0), thickness, cv2.LINE_AA)
                    traj = track.get_trajectory()
                    if len(traj) > 1:
                        for i in range(len(traj) - 1):
                            alpha = (i + 1) / len(traj)
                            t_color = tuple(int(c * alpha) for c in color)
                            cv2.line(frame_vis, traj[i], traj[i + 1], t_color, 1)

                frame_vis = counter.draw_lines(frame_vis, show_counts=True)
                elapsed_now = time.time() - proc_start
                live_fps = frame_count / max(elapsed_now, 0.001)
                cv2.putText(frame_vis,
                            f"FPS: {live_fps:.1f}  Frame: {frame_count}/{total_frames}",
                            (10, 22), cv2.FONT_HERSHEY_SIMPLEX, 0.55,
                            (255, 255, 255), 1, cv2.LINE_AA)

                if save_video:
                    out.write(frame_vis)

                if show_visualizations and use_opencv_window:
                    cv2.imshow("Traffic Analysis — procesando (Q para cerrar)", frame_vis)
                    if cv2.waitKey(1) & 0xFF == ord('q'):
                        break

            if show_visualizations and frame_count % 10 == 0:
                progress = frame_count / total_frames
                progress_bar.progress(progress)
                elapsed = frame_count / fps
                status_text.text(
                    f"Frame {frame_count}/{total_frames}  "
                    f"({progress * 100:.1f}%)  —  {elapsed:.1f}s procesados"
                )
                current_stats = counter.get_statistics()
                total_counts = current_stats.get('total_counts', {})
                if total_counts:
                    counts_es = {}
                    for cls_en, cnt in total_counts.items():
                        cls_es = OBJECT_CLASSES.get(cls_en, {}).get('name', cls_en)
                        counts_es[cls_es] = cnt
                    proc_fps = frame_count / max(time.time() - proc_start, 0.001)
                    with metrics_slot.container():
                        live_metrics_panel(counts=counts_es, fps=proc_fps,
                                           elapsed=time.time() - proc_start)

                if frame_count % 30 == 0:
                    scale = st.session_state.get('canvas_scale_factor', 1.0)
                    if scale and scale > 1.0 and st.session_state.get('frame_for_lines') is not None:
                        disp_w = st.session_state['frame_for_lines'].shape[1]
                        disp_h = st.session_state['frame_for_lines'].shape[0]
                        frame_disp = cv2.resize(frame_vis, (disp_w, disp_h),
                                                interpolation=cv2.INTER_AREA)
                        frame_rgb = cv2.cvtColor(frame_disp, cv2.COLOR_BGR2RGB)
                        video_placeholder.image(frame_rgb, caption=f"Frame {frame_count}",
                                                width=disp_w)
                    else:
                        frame_rgb = cv2.cvtColor(frame_vis, cv2.COLOR_BGR2RGB)
                        video_placeholder.image(frame_rgb, caption=f"Frame {frame_count}",
                                                use_column_width=True)

                if frame_count % 60 == 0:
                    with stats_placeholder.container():
                        section_title("Estadísticas en tiempo real")
                        c1, c2, c3 = st.columns(3)
                        c1.metric("Cruces registrados", current_stats['total_crossings'])
                        c2.metric("Tracks activos", len(valid_tracks))
                        c3.metric("Tiempo procesado", f"{elapsed:.1f}s")

        cap.release()
        if save_video:
            out.release()

        statistics = counter.get_statistics()
        time_series = counter.get_time_series_data(interval_seconds=60)

        if show_visualizations:
            progress_bar.progress(1.0)
            status_text.text("Procesamiento completado.")
            flicker_analyzer.report()

        return True, output_video_path, statistics, all_crossings, time_series

    except Exception as e:
        logger.error(f"Error en procesamiento: {e}")
        st.error(f"Error durante el procesamiento: {e}")
        return False, None, None, [], None


# ==================== INTERFAZ PRINCIPAL ====================

def main():

    header(
        title="Traffic Analysis Tool",
        subtitle="Análisis vehicular con YOLOv8 · Lima, Perú",
        badge="v1.0 · YOLOv8n"
    )

    # ── SIDEBAR ──────────────────────────────────────────────
    with st.sidebar:
        sidebar_brand()
        step_indicator(
            steps=["Cargar video", "Inicializar detector", "Definir líneas", "Procesar"],
            current=_step_actual()
        )
        st.markdown("---")
        sidebar_label("1 · Video")

        video_file = st.file_uploader(
            "Selecciona un video",
            type=['mp4', 'avi', 'mov', 'mkv'],
            help="MP4, AVI, MOV o MKV"
        )

        if video_file is not None and not st.session_state.video_uploaded:
            with st.spinner("Cargando video..."):
                result = load_video(video_file)
                if result:
                    st.session_state.video_path, st.session_state.video_properties = result
                    st.session_state.video_uploaded = True
                    raw_frame = get_first_frame(st.session_state.video_path)
                    if raw_frame is not None:
                        st.session_state.frame_for_lines = raw_frame
                        st.session_state.frame_for_lines_raw = raw_frame
                        st.session_state.canvas_scale_factor = 1.0
                    else:
                        st.session_state.frame_for_lines = None
                        st.session_state.frame_for_lines_raw = None
                        st.session_state.canvas_scale_factor = 1.0
                    st.session_state.output_dirs = create_output_dirs()
                    st.success("Video cargado.")

        if st.session_state.video_uploaded:
            video_info_card(st.session_state.video_properties)
            est = estimate_processing_time(st.session_state.video_path)
            st.caption(f"Tiempo estimado: {est / 60:.1f} min")

        st.markdown("---")
        sidebar_label("2 · Detector")

        confidence = st.slider("Confianza mínima", min_value=0.1, max_value=1.0,
                               value=0.5, step=0.05)
        model_size = st.selectbox("Tamaño del modelo", options=['n', 's', 'm', 'l'], index=0)

        sidebar_label("Clases a detectar")
        available_classes = list(OBJECT_CLASSES.keys())
        class_names_spanish = [OBJECT_CLASSES[c]['name'] for c in available_classes]
        selected_classes_es = st.multiselect("Categorías", options=class_names_spanish,
                                             default=class_names_spanish)
        selected_classes = [k for k, v in OBJECT_CLASSES.items()
                            if v['name'] in selected_classes_es]
        use_peruvian = st.checkbox("Usar modelo peruano", value=True,
                                   help="vehiculos_lima_v1.pt — entrenado con clases de Lima")

        det_status = "ready" if st.session_state.detector else "inactive"
        status_badge("Detector listo" if st.session_state.detector else "Sin inicializar",
                     det_status)

        if st.button("Inicializar detector", type="primary"):
            with st.spinner("Inicializando..."):
                try:
                    st.session_state.detector = create_detector(
                        confidence=confidence,
                        model_size=model_size,
                        classes=selected_classes if selected_classes else None,
                        use_peruvian_model=use_peruvian
                    )
                    st.session_state.tracker = ObjectTracker(
                        max_age=10, min_hits=3, iou_threshold=0.3
                    )
                    if st.session_state.counter is None:
                        fps_vid = (st.session_state.video_properties['fps']
                                   if st.session_state.video_properties else 30)
                        st.session_state.counter = TrafficCounter(fps=fps_vid)
                    st.success("Detector y tracker listos.")
                    logger.info("Detector inicializado correctamente")
                except Exception as e:
                    st.error(f"Error: {e}")
                    logger.error(f"Error al inicializar detector: {e}")

        st.markdown("---")
        with st.expander("Acerca de"):
            st.caption("Traffic Analysis Tool v1.0\nYOLOv8 · Tracking multi-objeto · "
                       "Líneas de conteo · Excel / CSV\nStreamlit + OpenCV + PyTorch")

    # ==================== TABS PRINCIPALES ====================

    tab1, tab2, tab3, tab4 = st.tabs(["Líneas", "Procesar", "Resultados", "Exportar"])

    # ── TAB 1: Definir Líneas ─────────────────────────────────
    with tab1:
        section_title("Definir líneas de conteo")

        if not st.session_state.video_uploaded:
            empty_state(
                icon="📹",
                title="Sin video cargado",
                description="Sube un video desde el sidebar para definir las líneas de conteo."
            )
        else:
            # Cabecera del visor
            props = st.session_state.video_properties or {}
            w, h = props.get('width', '—'), props.get('height', '—')
            n_lines = len(st.session_state.counting_lines)
            display_w, display_h = (
                st.session_state.frame_for_lines.shape[1],
                st.session_state.frame_for_lines.shape[0]
            ) if st.session_state.frame_for_lines is not None else (w, h)

            st.markdown(f"""
            <div style="display:flex;align-items:center;justify-content:space-between;
                        background:#181C24;border:1px solid #1E2433;
                        border-radius:10px 10px 0 0;padding:10px 16px;border-bottom:none;">
                <div style="display:flex;align-items:center;gap:8px;">
                    <span style="width:8px;height:8px;border-radius:50%;background:#22C55E;
                                 display:inline-block;"></span>
                    <span style="font-size:0.78rem;font-weight:600;color:#94A3B8;
                                 letter-spacing:0.04em;">FRAME DE REFERENCIA</span>
                </div>
                <div style="display:flex;gap:10px;flex-wrap:wrap;">
                    <span style="font-size:0.7rem;color:#475569;background:#111318;
                                 border:1px solid #1E2433;border-radius:5px;
                                 padding:2px 8px;">{w}×{h}</span>
                    <span style="font-size:0.7rem;color:#94A3B8;background:#111318;
                                 border:1px solid #1E2433;border-radius:5px;
                                 padding:2px 8px;">Canvas {display_w}×{display_h}</span>
                    <span style="font-size:0.7rem;color:#F5A623;
                                 background:rgba(245,166,35,0.1);border:1px solid #7A5210;
                                 border-radius:5px;padding:2px 8px;">
                        {n_lines} línea{'s' if n_lines != 1 else ''}
                    </span>
                </div>
            </div>
            """, unsafe_allow_html=True)

            # Canvas ancho completo
            if 'manual_canvas_key' not in st.session_state:
                st.session_state.manual_canvas_key = "manual_lines_canvas"

            if st.session_state.frame_for_lines is not None:
                st.markdown("""
                <div style="border:1px solid #1E2433;border-radius:0 0 10px 10px;overflow:hidden;">
                """, unsafe_allow_html=True)

                drawing_tool = DrawingTool(
                    st.session_state.frame_for_lines,
                    canvas_key=st.session_state.manual_canvas_key
                )
                drawn_lines = drawing_tool.draw_lines([])

                pending_lines = []
                if drawn_lines is not None:
                    for drawn in drawn_lines:
                        if 'coords' in drawn and len(drawn['coords']) == 2:
                            coords = drawn['coords']
                            hex_color = drawn.get('color', '#F5A623')
                            if isinstance(hex_color, str) and hex_color.startswith('#'):
                                rgb = tuple(int(hex_color.lstrip('#')[i:i+2], 16)
                                            for i in (0, 2, 4))
                                bgr = (rgb[2], rgb[1], rgb[0])
                            else:
                                bgr = drawn.get('color', (0, 255, 0))
                            orig_w = st.session_state.frame_for_lines_raw.shape[1]
                            canvas_scale = orig_w / 800 if orig_w > 800 else 1.0
                            start = (int(coords[0][0] * canvas_scale),
                                     int(coords[0][1] * canvas_scale))
                            end = (int(coords[1][0] * canvas_scale),
                                   int(coords[1][1] * canvas_scale))
                            pending_lines.append({
                                'name': drawn.get('name', f"Línea {len(pending_lines)+1}"),
                                'start': start,
                                'end': end,
                                'color': bgr,
                                'direction': drawn.get('direction', '')
                            })

                st.markdown("</div>", unsafe_allow_html=True)

                if pending_lines:
                    st.markdown("""
                    <div style="margin-top:10px;background:#0A0C10;border:1px solid #1E2433;
                                 border-radius:8px;padding:10px 14px;">
                        <strong style="color:#F5A623;font-size:0.82rem;">
                            Líneas dibujadas pendientes
                        </strong>
                        <div style="color:#94A3B8;font-size:0.78rem;margin-top:4px;">
                            Haz clic en el botón para agregar estas líneas a la lista.
                        </div>
                    </div>
                    """, unsafe_allow_html=True)

                    bcol1, bcol2 = st.columns([2, 1])
                    with bcol1:
                        if st.button("✚ Agregar líneas dibujadas", key="add_drawn_lines",
                                     type="primary"):
                            existing_coords = {
                                (tuple(l['start']), tuple(l['end']))
                                for l in st.session_state.counting_lines
                            }
                            added = 0
                            for p in pending_lines:
                                pair = (tuple(p['start']), tuple(p['end']))
                                if pair not in existing_coords:
                                    st.session_state.counting_lines.append(p)
                                    existing_coords.add(pair)
                                    added += 1
                            if added:
                                st.success(f"Se agregaron {added} línea(s).")
                            else:
                                st.info("No hay nuevas líneas.")
                            st.session_state.manual_canvas_key = \
                                f"manual_lines_canvas_{time.time()}"
                    with bcol2:
                        if st.button("🗑 Limpiar canvas", key="clear_manual_canvas"):
                            st.session_state.manual_canvas_key = \
                                f"manual_lines_canvas_{time.time()}"

            else:
                st.warning("No se cargó el frame de referencia.")


            # ── Panel de líneas DEBAJO del canvas ────────────
            n_lines = len(st.session_state.counting_lines)

            if 'lines_panel_collapsed' not in st.session_state:
                st.session_state.lines_panel_collapsed = False

            collapsed = st.session_state.lines_panel_collapsed
            border_r = "8px" if collapsed else "8px 8px 0 0"

            badge_color = '#F5A623' if n_lines > 0 else '#1E2433'
            badge_text_color = '#000' if n_lines > 0 else '#475569'

            if n_lines == 0:
                inner_html = '<span style="color:#334155;font-size:0.75rem;font-style:italic;">Sin líneas aún</span>'
            elif collapsed:
                tags = ""
                for line in st.session_state.counting_lines:
                    bgr = line['color']
                    hx = '#{:02x}{:02x}{:02x}'.format(bgr[2], bgr[1], bgr[0])
                    tags += (
                        f'<span style="display:inline-flex;align-items:center;gap:5px;'
                        f'background:#111318;border:1px solid #1E2433;border-radius:20px;'
                        f'padding:3px 10px;font-size:0.72rem;color:#94A3B8;margin-right:4px;">'
                        f'<span style="width:7px;height:7px;border-radius:50%;'
                        f'background:{hx};display:inline-block;"></span>'
                        f'{line["name"]}</span>'
                    )
                inner_html = tags
            else:
                inner_html = ""

            st.markdown(f"""
            <div style="margin-top:12px;background:#0D1017;border:1px solid #1E2433;
                        border-radius:{border_r};padding:10px 14px;
                        display:flex;align-items:center;justify-content:space-between;">
                <div style="display:flex;align-items:center;gap:10px;flex-wrap:wrap;">
                    <div style="display:flex;align-items:center;gap:7px;">
                        <span style="width:3px;height:13px;background:#F5A623;
                                    border-radius:2px;display:inline-block;"></span>
                        <span style="font-size:0.68rem;font-weight:600;letter-spacing:.1em;
                                    text-transform:uppercase;color:#475569;">
                            Líneas definidas
                        </span>
                        <span style="background:{badge_color};color:{badge_text_color};
                                    font-size:0.7rem;font-weight:700;padding:1px 8px;
                                    border-radius:20px;">{n_lines}</span>
                    </div>
                    {inner_html}
                </div>
            </div>
            """, unsafe_allow_html=True)

            toggle_label = "▲ Colapsar" if not collapsed else "▼ Expandir"
            if st.button(toggle_label, key="toggle_lines_panel"):
                st.session_state.lines_panel_collapsed = not collapsed
                st.rerun()

            # Cuerpo del panel — cards_html se define AQUÍ
            if not collapsed and n_lines > 0:
                DIR_STYLES = {
                    'N-S': ('#22c55e', 'rgba(34,197,94,0.13)', '↓'),
                    'S-N': ('#f59e0b', 'rgba(245,158,11,0.13)', '↑'),
                    'E-O': ('#3b82f6', 'rgba(59,130,246,0.13)', '→'),
                    'O-E': ('#a78bfa', 'rgba(167,139,250,0.13)', '←'),
                }

                cards_html = ""
                for line in st.session_state.counting_lines:
                    bgr = line['color']
                    hx = '#{:02x}{:02x}{:02x}'.format(bgr[2], bgr[1], bgr[0])
                    direction = line.get('direction', 'N-S')
                    dc, db, arrow = DIR_STYLES.get(
                        direction, ('#94a3b8', 'rgba(148,163,184,0.1)', '→'))
                    sx, sy = line['start']
                    ex, ey = line['end']
                    cards_html += (
                        f'<div style="background:#111318;border:1px solid #1E2433;'
                        f'border-left:3px solid {hx};border-radius:8px;'
                        f'padding:9px 12px;min-width:200px;flex:1;">'
                        f'<div style="display:flex;align-items:center;'
                        f'justify-content:space-between;margin-bottom:6px;">'
                        f'<div style="display:flex;align-items:center;gap:6px;">'
                        f'<div style="width:8px;height:8px;border-radius:50%;background:{hx};"></div>'
                        f'<span style="font-size:0.78rem;font-weight:600;color:#E2E8F0;">{line["name"]}</span>'
                        f'</div>'
                        f'<span style="background:{db};color:{dc};font-size:0.62rem;'
                        f'font-weight:600;padding:2px 7px;border-radius:20px;">{arrow} {direction}</span>'
                        f'</div>'
                        f'<div style="background:#0A0C10;border-radius:5px;padding:5px 9px;'
                        f'display:flex;justify-content:space-between;align-items:center;">'
                        f'<div>'
                        f'<div style="font-size:0.58rem;color:#334155;text-transform:uppercase;letter-spacing:.06em;">inicio</div>'
                        f'<div style="font-size:0.7rem;color:#64748B;font-family:monospace;">{sx}, {sy}</div>'
                        f'</div>'
                        f'<span style="color:#1E2433;font-size:0.9rem;">⟶</span>'
                        f'<div style="text-align:right;">'
                        f'<div style="font-size:0.58rem;color:#334155;text-transform:uppercase;letter-spacing:.06em;">fin</div>'
                        f'<div style="font-size:0.7rem;color:#64748B;font-family:monospace;">{ex}, {ey}</div>'
                        f'</div>'
                        f'</div>'
                        f'</div>'
                    )

                # Ahora sí, cards_html está definido
                components.html(
                    '<div style="background:#0A0C10;border:1px solid #1E2433;border-top:none;'
                    'border-radius:0 0 8px 8px;padding:10px;display:flex;gap:8px;flex-wrap:wrap;">'
                    + cards_html +
                    '</div>',
                    height=max(150, 160 * n_lines),
                    scrolling=False
                )

                # Botones eliminar
                del_cols = st.columns(min(n_lines, 4))
                for idx, line in enumerate(st.session_state.counting_lines):
                    with del_cols[idx % min(n_lines, 4)]:
                        if st.button(f"✕ {line['name']}",
                                     key=f"del_{idx}_{line['name']}_{line['start']}"):
                            st.session_state.counting_lines.pop(idx)
                            st.rerun()

    # ── TAB 2: Procesar ──────────────────────────────────────
    with tab2:
        section_title("Procesamiento de video")

        ok_video = st.session_state.video_uploaded
        ok_detector = st.session_state.detector is not None
        ok_lines = len(st.session_state.counting_lines) > 0

        c1, c2, c3 = st.columns(3)
        with c1:
            status_badge("Video cargado", "ready" if ok_video else "pending")
        with c2:
            status_badge("Detector listo", "ready" if ok_detector else "pending")
        with c3:
            status_badge("Líneas listas", "ready" if ok_lines else "pending")

        st.markdown("")

        if not (ok_video and ok_detector and ok_lines):
            empty_state(icon="⚙️", title="Configuración incompleta",
                        description="Completa los 3 pasos del sidebar antes de procesar.")
        else:
            vinfo = get_video_info(st.session_state.video_path)
            dur_str = format_duration(vinfo["duration_s"])
            use_chunks = needs_chunking(st.session_state.video_path, threshold_minutes=30)
            has_ffmpeg = ffmpeg_available()

            if use_chunks:
                chunker = VideoChunker(st.session_state.video_path, chunk_minutes=15)
                n_chunks = chunker.total_chunks
                chunk_info = chunker.get_chunk_info()
                est_proc_min = n_chunks * 3
            else:
                n_chunks = 1
                chunk_info = []

            st.markdown(f"""
            <div style="background:#111318;border:1px solid #1E2433;border-radius:12px;
                        padding:16px 20px;margin-bottom:16px;">
                <div style="display:flex;align-items:center;justify-content:space-between;
                            flex-wrap:wrap;gap:12px;">
                    <div style="display:flex;align-items:center;gap:14px;">
                        <div style="font-size:1.8rem;opacity:0.7;">🎬</div>
                        <div>
                            <div style="font-size:0.84rem;font-weight:600;color:#F1F5F9;">
                                {os.path.basename(st.session_state.video_path).split('_')[-1]
                                 if '_' in os.path.basename(st.session_state.video_path)
                                 else 'video.mp4'}
                            </div>
                            <div style="font-size:0.72rem;color:#475569;margin-top:3px;">
                                {vinfo["width"]}×{vinfo["height"]} · {vinfo["fps"]:.0f}fps ·
                                {vinfo["size_mb"]:.0f}MB
                            </div>
                        </div>
                    </div>
                    <div style="display:flex;gap:10px;flex-wrap:wrap;">
                        <div style="background:#0A0C10;border:1px solid #1E2433;
                                    border-radius:8px;padding:8px 14px;text-align:center;">
                            <div style="font-size:0.62rem;font-weight:600;letter-spacing:0.1em;
                                        text-transform:uppercase;color:#475569;margin-bottom:2px;">
                                Duración
                            </div>
                            <div style="font-size:1rem;font-weight:500;color:#F5A623;">
                                {dur_str}
                            </div>
                        </div>
                        <div style="background:#0A0C10;border:1px solid #1E2433;
                                    border-radius:8px;padding:8px 14px;text-align:center;">
                            <div style="font-size:0.62rem;font-weight:600;letter-spacing:0.1em;
                                        text-transform:uppercase;color:#475569;margin-bottom:2px;">
                                Modo
                            </div>
                            <div style="font-size:1rem;font-weight:500;
                                        color:{'#22C55E' if use_chunks else '#3B82F6'};">
                                {'Chunks ×' + str(n_chunks) if use_chunks else 'Directo'}
                            </div>
                        </div>
                        <div style="background:#0A0C10;border:1px solid #1E2433;
                                    border-radius:8px;padding:8px 14px;text-align:center;">
                            <div style="font-size:0.62rem;font-weight:600;letter-spacing:0.1em;
                                        text-transform:uppercase;color:#475569;margin-bottom:2px;">
                                Est. proceso
                            </div>
                            <div style="font-size:1rem;font-weight:500;color:#94A3B8;">
                                ~{est_proc_min if use_chunks
                                  else int(vinfo["duration_min"] * 0.3)} min
                            </div>
                        </div>
                    </div>
                </div>
            </div>
            """, unsafe_allow_html=True)

            if use_chunks and not has_ffmpeg:
                st.warning(f"Video largo ({dur_str}) — ffmpeg no instalado. "
                           f"Instala con: `winget install ffmpeg`")

            if use_chunks and has_ffmpeg and chunk_info:
                with st.expander(f"Ver plan — {n_chunks} chunks de 15 min"):
                    rows_html = "".join([
                        f'<div style="display:flex;justify-content:space-between;'
                        f'padding:6px 0;border-bottom:1px solid #1E2433;font-size:0.75rem;">'
                        f'<span style="color:#475569;">Chunk {ci["index"]+1:02d}</span>'
                        f'<span style="color:#94A3B8;">{ci["start_str"]} → {ci["end_str"]}</span>'
                        f'<span style="color:#475569;">{format_duration(ci["duration_s"])}</span>'
                        f'</div>'
                        for ci in chunk_info
                    ])
                    st.markdown(f"""
                    <div style="background:#0A0C10;border:1px solid #1E2433;border-radius:8px;
                                padding:12px 16px;max-height:200px;overflow-y:auto;">
                        {rows_html}
                    </div>""", unsafe_allow_html=True)

            col1, col2 = st.columns(2)
            with col1:
                save_video = st.checkbox("Guardar video procesado", value=False)
            with col2:
                show_viz = st.checkbox("Visualización en tiempo real", value=True)

            if opencv_gui_available():
                use_opencv_window = st.checkbox("Mostrar ventana OpenCV local", value=False)
            else:
                use_opencv_window = False
                st.warning("OpenCV GUI no disponible.")

            st.markdown("")

            if st.button("Iniciar procesamiento", type="primary", use_container_width=True):
                if not st.session_state.counting_lines:
                    st.error("❌ Debes agregar al menos una línea antes de procesar.")
                    st.stop()

                section_title("Procesando…")
                st.session_state.counter.clear_lines()

                added_lines = 0
                for line in st.session_state.counting_lines:
                    start = tuple(line['start']) if not isinstance(line['start'], tuple) \
                        else line['start']
                    end = tuple(line['end']) if not isinstance(line['end'], tuple) \
                        else line['end']
                    color = tuple(line['color']) if not isinstance(line['color'], tuple) \
                        else line['color']
                    st.session_state.counter.add_line(
                        start=start, end=end, name=line['name'], color=color)
                    added_lines += 1

                st.info(f"✓ {added_lines} línea(s) agregada(s) al contador")
                t0 = time.time()

                if use_chunks and has_ffmpeg:
                    chunk_bar = st.progress(0)
                    chunk_status = st.empty()
                    all_stats = []
                    all_crossings = []
                    failed_chunks = []
                    try:
                        chunker = VideoChunker(
                            st.session_state.video_path, chunk_minutes=15,
                            output_dir=os.path.join(
                                st.session_state.output_dirs['base'], "chunks"))
                        chunk_paths = chunker.split()
                        for i, chunk_path in enumerate(chunk_paths):
                            lbl = chunker.chunk_label(i)
                            chunk_status.markdown(
                                f'<div style="color:#F5A623;font-size:0.8rem;">▶ {lbl}</div>',
                                unsafe_allow_html=True)
                            success, _, stats, crossings, time_series = process_video(
                                chunk_path, st.session_state.detector,
                                st.session_state.tracker, st.session_state.counter,
                                save_video=False, show_visualizations=show_viz,
                                use_opencv_window=use_opencv_window)
                            if success and stats:
                                all_stats.append(stats)
                                all_crossings.extend(crossings)
                            else:
                                failed_chunks.append(lbl)
                            chunker.delete_chunk(chunk_path)
                            chunk_bar.progress((i + 1) / len(chunk_paths))

                        chunk_status.empty()
                        final_stats = consolidate_stats(all_stats)
                        final_crossings = consolidate_crossings([all_crossings])
                        proc_time = time.time() - t0
                        st.session_state.processing_complete = True
                        st.session_state.statistics = final_stats
                        st.session_state.crossings = final_crossings
                        st.session_state.time_series = None
                        st.session_state.processed_video_path = None
                        if failed_chunks:
                            st.warning(f"Completado con chunks fallidos: {', '.join(failed_chunks)}")
                        else:
                            st.success(f"✓ {n_chunks} chunks en {proc_time/60:.1f} min.")
                    except Exception as e:
                        st.error(f"Error en chunks: {e}")
                else:
                    success, vid_path, stats, crossings, time_series = process_video(
                        st.session_state.video_path, st.session_state.detector,
                        st.session_state.tracker, st.session_state.counter,
                        save_video=save_video, show_visualizations=show_viz,
                        use_opencv_window=use_opencv_window)
                    proc_time = time.time() - t0
                    if success:
                        st.session_state.processing_complete = True
                        st.session_state.statistics = stats
                        st.session_state.crossings = crossings
                        st.session_state.time_series = time_series
                        st.session_state.processed_video_path = vid_path
                        st.success(f"✓ Completado en {proc_time/60:.1f} min.")
                    else:
                        st.error("Error durante el procesamiento.")

                if st.session_state.processing_complete:
                    s = st.session_state.statistics
                    section_title("Resumen rápido")
                    r1, r2, r3, r4 = st.columns(4)
                    r1.metric("Cruces totales", s.get('total_crossings', 0))
                    r2.metric("Líneas usadas", s.get('total_lines', 0))
                    r3.metric("Tiempo analizado", f"{s.get('elapsed_minutes', 0):.1f} min")
                    r4.metric("Objetos únicos", sum(s.get('total_counts', {}).values()))
                    if (st.session_state.processed_video_path and
                            os.path.exists(st.session_state.processed_video_path)):
                        section_title("Video procesado")
                        video_player(st.session_state.processed_video_path, height=400)

    # ── TAB 3: Resultados ────────────────────────────────────
    with tab3:
        section_title("Resultados del análisis")

        if not st.session_state.processing_complete:
            empty_state(icon="📊", title="Sin resultados aún",
                        description="Procesa un video primero.")
        else:
            stats = st.session_state.statistics
            crossings = st.session_state.crossings
            total = sum(stats['total_counts'].values())

            section_title("Resumen general")
            kpi1, kpi2, kpi3, kpi4 = st.columns(4)
            with kpi1:
                metric_card("Cruces totales", stats['total_crossings'],
                            subtitle="eventos registrados")
            with kpi2:
                metric_card("Líneas activas", stats['total_lines'],
                            subtitle="líneas de conteo")
            with kpi3:
                metric_card("Tiempo analizado", f"{stats['elapsed_minutes']:.1f} min",
                            subtitle="duración del video")
            with kpi4:
                metric_card("Objetos únicos", total, subtitle="todos los tipos")

            st.markdown("")
            section_title("Conteos por categoría")
            total_counts = stats['total_counts']

            if total_counts:
                CLASS_VEHICLE_MAP = {
                    'Auto': 'car', 'Moto': 'moto', 'Bus': 'bus',
                    'Camión': 'truck', 'Peatón': 'person', 'Bicicleta': 'bicycle',
                }
                cols = st.columns(len(total_counts))
                for i, (cls_en, count) in enumerate(total_counts.items()):
                    cls_es = OBJECT_CLASSES.get(cls_en, {}).get('name', cls_en)
                    v_cls = CLASS_VEHICLE_MAP.get(cls_es, '')
                    total_all = sum(total_counts.values())
                    pct = f"{count/total_all*100:.0f}%" if total_all > 0 else "—"
                    with cols[i]:
                        metric_card(cls_es, count, subtitle=pct, vehicle_class=v_cls)

                df_counts = pd.DataFrame({
                    'Categoría': [OBJECT_CLASSES.get(k, {}).get('name', k)
                                  for k in total_counts.keys()],
                    'Conteo': list(total_counts.values())
                })
                st.bar_chart(df_counts.set_index('Categoría'))

            st.markdown("---")
            section_title("Conteos por línea")
            for line_info in stats['counts_by_line']:
                with st.expander(
                        f"{line_info['line_name']}  —  total: {line_info['total_count']}"):
                    rows = []
                    for class_name, directions in line_info['counts_by_class'].items():
                        rows.append({
                            'Categoría': class_name,
                            'Total': directions['total'],
                            'Arriba→Abajo': directions.get('up_to_down', 0),
                            'Abajo→Arriba': directions.get('down_to_up', 0),
                            'Izq→Der': directions.get('left_to_right', 0),
                            'Der→Izq': directions.get('right_to_left', 0),
                        })
                    if rows:
                        st.dataframe(pd.DataFrame(rows), use_container_width=True,
                                     hide_index=True)

            st.markdown("---")
            section_title("Detalle de cruces")
            if crossings:
                df_crossings = pd.DataFrame([
                    {
                        'Timestamp': f"{c['timestamp']:.2f}s",
                        'Track ID': c['track_id'],
                        'Categoría': c['class_spanish'],
                        'Línea': c['line_name'],
                        'Dirección': c['direction'],
                    }
                    for c in crossings[:100]
                ])
                st.dataframe(df_crossings, use_container_width=True, hide_index=True)
                if len(crossings) > 100:
                    st.caption(f"Mostrando 100 de {len(crossings)} cruces totales.")
            else:
                st.info("No se detectaron cruces.")

            st.markdown("---")
            if st.button("Generar visualizaciones", type="primary"):
                with st.spinner("Generando gráficos..."):
                    if st.session_state.output_dirs is None:
                        st.session_state.output_dirs = create_output_dirs()
                    visualizer = TrafficVisualizer(
                        output_dir=st.session_state.output_dirs['visualizations'])
                    frame_shape = (
                        st.session_state.video_properties['height'],
                        st.session_state.video_properties['width']
                    )
                    viz_files = visualizer.generate_all_visualizations(
                        stats, crossings, st.session_state.time_series, frame_shape)
                    st.success(f"{len(viz_files)} visualizaciones generadas.")
                    for viz_name, viz_path in viz_files.items():
                        if os.path.exists(viz_path):
                            st.image(viz_path, caption=viz_name, use_column_width=True)

        section_title("📈 Tendencias y Análisis")
        if 'time_series' in st.session_state and st.session_state.time_series:
            ts = st.session_state.time_series
            counts = ts.get('counts', {})
            col1, col2, col3 = st.columns(3)
            with col1:
                total = sum(sum(v) for v in counts.values())
                st.metric("Total General", f"{total:,}")
            with col2:
                avg = total / len(ts.get('intervals', [1]))
                st.metric("Promedio por Intervalo", f"{avg:.1f}")
            with col3:
                max_val = max(sum(v) for v in zip(*counts.values())) if counts else 0
                st.metric("Pico Máximo", f"{max_val}")

    # ── TAB 4: Exportar ──────────────────────────────────────
    with tab4:
        section_title("📥 Exportar Resultados")

        if not st.session_state.processing_complete:
            empty_state(icon="📥", title="Sin datos para exportar",
                        description="Procesa un video primero.")
        else:
            col1, col2, col3 = st.columns(3)

            with col1:
                st.markdown("""
                <div style="background:#111318;border:1px solid #1E2433;border-radius:10px;
                            padding:20px;text-align:center;">
                    <div style="font-size:2.5rem;margin-bottom:10px;">📊</div>
                    <h4>Excel Completo</h4>
                    <p style="color:#94A3B8;font-size:0.8rem;">Resumen y conteos por línea</p>
                </div>
                """, unsafe_allow_html=True)
                st.write("")
                if st.button("📥 Generar Excel", key="btn_excel", type="primary",
                             use_container_width=True):
                    with st.spinner("Generando Excel..."):
                        exporter = DataExporter(
                            output_dir=st.session_state.output_dirs['exports'],
                            video_name="traffic_analysis")
                        excel_path = exporter.export_to_excel(
                            st.session_state.statistics, st.session_state.crossings,
                            st.session_state.time_series, st.session_state.video_properties)
                        st.success("✅ Excel generado.")
                        with open(excel_path, 'rb') as f:
                            st.download_button(
                                label="⬇️ Descargar Excel", data=f,
                                file_name=os.path.basename(excel_path),
                                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                                use_container_width=True)

            with col2:
                st.markdown("""
                <div style="background:#111318;border:1px solid #1E2433;border-radius:10px;
                            padding:20px;text-align:center;">
                    <div style="font-size:2.5rem;margin-bottom:10px;">📄</div>
                    <h4>CSV Datos Crudos</h4>
                    <p style="color:#94A3B8;font-size:0.8rem;">Datos para análisis avanzado</p>
                </div>
                """, unsafe_allow_html=True)
                st.write("")
                if st.button("📥 Generar CSV", key="btn_csv", type="primary",
                             use_container_width=True):
                    with st.spinner("Generando CSV..."):
                        exporter = DataExporter(
                            output_dir=st.session_state.output_dirs['exports'],
                            video_name="traffic_analysis")
                        csv_path = exporter.export_to_csv(st.session_state.crossings)
                        st.success("✅ CSV generado.")
                        with open(csv_path, 'rb') as f:
                            st.download_button(
                                label="⬇️ Descargar CSV", data=f,
                                file_name=os.path.basename(csv_path),
                                mime="text/csv", use_container_width=True)

            with col3:
                st.markdown("""
                <div style="background:#111318;border:1px solid #1E2433;border-radius:10px;
                            padding:20px;text-align:center;">
                    <div style="font-size:2.5rem;margin-bottom:10px;">📦</div>
                    <h4>Exportar Todo</h4>
                    <p style="color:#94A3B8;font-size:0.8rem;">Excel + CSV + series temporales</p>
                </div>
                """, unsafe_allow_html=True)
                st.write("")
                if st.button("📦 Exportar Todo", key="btn_all", type="primary",
                             use_container_width=True):
                    with st.spinner("Generando todos los archivos..."):
                        exporter = DataExporter(
                            output_dir=st.session_state.output_dirs['exports'],
                            video_name="traffic_analysis")
                        files = exporter.export_all(
                            st.session_state.statistics, st.session_state.crossings,
                            st.session_state.time_series, st.session_state.video_properties)
                        st.success(f"✅ {len(files)} archivos generados.")

            st.markdown("---")
            section_title("📋 Reporte MTC Oficial")

            col_info, col_form = st.columns([1, 1])
            with col_info:
                st.markdown("""
                <div style="background:#111318;border:1px solid #1E2433;border-radius:10px;
                            padding:20px;">
                    <div style="font-size:2rem;margin-bottom:10px;">🏛️</div>
                    <p style="color:#94A3B8;font-size:0.82rem;line-height:1.6;">
                        Formato oficial del
                        <strong style="color:#F1F5F9;">Ministerio de Transportes y
                        Comunicaciones</strong> para estudios de aforo vehicular.
                        Intervalos de 15 minutos, totales por tipo y sección de firmas.
                    </p>
                </div>
                """, unsafe_allow_html=True)

            with col_form:
                estacion_input = st.text_input("Estación",
                                               value="Av. República de Panamá - Vía Expresa")
                codigo_input = st.text_input("Código",
                                             value=f"MTC-{datetime.now().strftime('%Y%m%d')}-001")
                tramo_input = st.text_input("Tramo", value="Tramo de estudio")
                ubicacion_input = st.text_input("Ubicación", value="Intersección principal")
                sentido_input = st.selectbox("Sentido", ["N-S", "S-N", "E-O", "O-E"])
                hora_inicio_input = st.text_input("Hora inicio del video", value="06:00")
                supervisor_input = st.text_input("Supervisor", value="")
                coord_input = st.text_input("Coordinador", value="")

            st.write("")
            if st.button("📋 Generar Reporte MTC", type="primary", use_container_width=True):
                with st.spinner("Generando reporte MTC..."):
                    try:
                        if st.session_state.output_dirs is None:
                            st.session_state.output_dirs = create_output_dirs()

                        VEHICLE_TYPES_MTC = [
                            'Auto', 'Moto', 'Bus', 'Microbus', 'Omnibus',
                            'Omnibus Articulado', 'Camion', 'Camioneta',
                            'Combi', 'Furgon', 'Minivan', 'Van',
                            'Mototaxi', 'Trailer', 'Trailer Doble', 'Especiales', 'Peaton'
                        ]
                        CLASE_A_MTC = {
                            'auto': 'Auto', 'moto': 'Moto', 'bus': 'Bus',
                            'microbus': 'Microbus', 'omnibus': 'Omnibus',
                            'omnibus-articulado': 'Omnibus Articulado',
                            'camion': 'Camion', 'camioneta': 'Camioneta',
                            'combi': 'Combi', 'furgon': 'Furgon',
                            'minivan': 'Minivan', 'van': 'Van',
                            'mototaxi': 'Mototaxi', 'trailer': 'Trailer',
                            'trailer doble': 'Trailer Doble',
                            'especiales': 'Especiales', 'peaton': 'Peaton',
                        }

                        video_start = datetime.combine(
                            datetime.now().date(),
                            datetime.strptime(hora_inicio_input, '%H:%M').time()
                        )
                        data_by_line = {}
                        for crossing in st.session_state.crossings:
                            ts = crossing.get('timestamp', 0)
                            cls = (crossing.get('class_spanish') or
                                   crossing.get('class_name') or '').lower().strip()
                            line_name = crossing.get('line_name', 'Sin_Linea')
                            interval_index = int(ts // 900)
                            interval_dt = video_start + timedelta(minutes=interval_index * 15)
                            interval_key = interval_dt.strftime('%H:%M')
                            if line_name not in data_by_line:
                                data_by_line[line_name] = {}
                            if interval_key not in data_by_line[line_name]:
                                data_by_line[line_name][interval_key] = {
                                    vt: 0 for vt in VEHICLE_TYPES_MTC}
                            mtc_type = CLASE_A_MTC.get(cls)
                            if mtc_type and mtc_type in data_by_line[line_name][interval_key]:
                                data_by_line[line_name][interval_key][mtc_type] += 1

                        if not data_by_line:
                            hora_key = datetime.strptime(
                                hora_inicio_input, '%H:%M').strftime('%H:%M')
                            data_by_line['Sin_Linea'] = {
                                hora_key: {vt: 0 for vt in VEHICLE_TYPES_MTC}}

                        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                        filename = f"Aforo_MTC_{codigo_input}_{timestamp}.xlsx"
                        output_path = os.path.join(
                            st.session_state.output_dirs['exports'], filename)

                        generator = ExcelAforoMTC(
                            estacion=estacion_input, codigo=codigo_input,
                            tramo=tramo_input, ubicacion=ubicacion_input,
                            sentido=sentido_input, dia=datetime.now().strftime("%A"),
                            fecha=datetime.now())
                        generator.generate(data_by_line, output_path,
                                           supervisor_input, coord_input)

                        st.success("✅ Reporte MTC generado.")
                        with open(output_path, 'rb') as f:
                            st.download_button(
                                label="⬇️ Descargar Reporte MTC", data=f,
                                file_name=filename,
                                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                                use_container_width=True)
                    except Exception as e:
                        st.error(f"Error generando reporte MTC: {e}")
                        logger.error(f"Error reporte MTC: {e}")

            st.markdown("---")
            if st.session_state.output_dirs:
                section_title("Archivos generados")
                st.code(st.session_state.output_dirs['base'])
                for subdir in ['exports', 'visualizations', 'videos']:
                    dir_path = st.session_state.output_dirs[subdir]
                    if os.path.exists(dir_path):
                        files = os.listdir(dir_path)
                        if files:
                            with st.expander(f"{subdir.upper()}  ({len(files)})"):
                                for f in files:
                                    st.text(f"  {f}")


if __name__ == "__main__":
    main()