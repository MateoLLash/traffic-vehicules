import streamlit as st
import cv2
import numpy as np
from pathlib import Path
import tempfile
import json
from datetime import datetime, timedelta
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

# Importar módulos propios
from config import *
from detector import Detector
from tracker import Tracker
from counter import Counter
from visualizer import Visualizer
from consolidator import VideoConsolidator
from excel_generator import ExcelGenerator
from template_manager import TemplateManager

# Configuración de la página
st.set_page_config(
    page_title="Sistema de Aforador Vehicular y Peatonal",
    page_icon="🚗",
    layout="wide",
    initial_sidebar_state="expanded"
)

# CSS personalizado para mejorar la apariencia
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        color: #1f77b4;
        text-align: center;
        margin-bottom: 2rem;
    }
    .metric-card {
        background-color: #f0f2f6;
        padding: 1rem;
        border-radius: 0.5rem;
        border-left: 4px solid #1f77b4;
    }
    .stButton>button {
        width: 100%;
    }
</style>
""", unsafe_allow_html=True)

# Inicializar session_state
if 'videos' not in st.session_state:
    st.session_state.videos = []
if 'zones' not in st.session_state:
    st.session_state.zones = []
if 'lines' not in st.session_state:
    st.session_state.lines = []
if 'processing_complete' not in st.session_state:
    st.session_state.processing_complete = False
if 'results' not in st.session_state:
    st.session_state.results = None
if 'current_frame' not in st.session_state:
    st.session_state.current_frame = None

# ==================== SIDEBAR ====================
with st.sidebar:
    st.image("https://placehold.co/200x80/1f77b4/white?text=AFORADOR+PRO", use_container_width=True)
    st.markdown("---")
    
    st.header("⚙️ Configuración del Sistema")
    
    # Selección de dispositivo
    device_option = st.selectbox(
        "Dispositivo de Procesamiento",
        ["CPU (AMD Ryzen 5 5600G)", "GPU (NVIDIA - Futuro)"],
        help="Actualmente optimizado para CPU. GPU se habilitará en futuras versiones."
    )
    
    # Configuración del modelo
    st.subheader("🎯 Modelo de Detección")
    model_size = st.selectbox(
        "Tamaño del Modelo",
        ["yolov8n.pt (Rápido)", "yolov8s.pt (Balanceado)", "yolov8m.pt (Preciso)"],
        help="Modelos más grandes = mayor precisión pero más lento"
    )
    
    confidence = st.slider(
        "Confianza Mínima",
        min_value=0.1,
        max_value=0.9,
        value=0.3,
        step=0.05,
        help="Umbral de confianza para detecciones"
    )
    
    st.markdown("---")
    
    # Gestión de plantillas
    st.subheader("📋 Plantillas de Intersecciones")
    templates = TemplateManager.list_templates()
    
    if templates:
        selected_template = st.selectbox("Cargar Plantilla", ["-- Nueva Configuración --"] + templates)
        if selected_template != "-- Nueva Configuración --":
            if st.button("🔄 Cargar Plantilla"):
                config_data, msg = TemplateManager.load_template(selected_template)
                if config_data:
                    st.session_state.zones = config_data.get('zones', [])
                    st.session_state.lines = config_data.get('lines', [])
                    st.success(msg)
                else:
                    st.error(msg)
    
    # Guardar plantilla actual
    template_name = st.text_input("Nombre de la Plantilla", placeholder="Ej: Av_Arequipa_Javier_Prado")
    if st.button("💾 Guardar Plantilla Actual"):
        if template_name:
            config_data = {
                'zones': st.session_state.zones,
                'lines': st.session_state.lines,
                'timestamp': datetime.now().isoformat()
            }
            success, msg = TemplateManager.save_template(template_name, config_data)
            if success:
                st.success(msg)
            else:
                st.error(msg)
        else:
            st.warning("Ingresa un nombre para la plantilla")
    
    st.markdown("---")
    st.info("💡 **Tip:** Guarda plantillas para reutilizar configuraciones en la misma intersección.")

# ==================== MAIN CONTENT ====================
st.markdown('<div class="main-header">🚗 Sistema de Aforador Vehicular y Peatonal</div>', unsafe_allow_html=True)

# Tabs principales
tab1, tab2, tab3 = st.tabs(["📹 Configuración de Videos", "⚡ Procesamiento", "📊 Resultados y Reportes"])

# ==================== TAB 1: CONFIGURACIÓN ====================
with tab1:
    st.header("1️⃣ Subir Videos de la Intersección")
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        uploaded_files = st.file_uploader(
            "Selecciona uno o más videos (máx. 200MB c/u)",
            type=['mp4', 'avi', 'mov', 'mkv'],
            accept_multiple_files=True,
            help="Sube videos consecutivos de la misma intersección para consolidar en un solo reporte"
        )
        
        if uploaded_files:
            st.session_state.videos = []
            for uploaded_file in uploaded_files:
                # Guardar temporalmente
                tfile = tempfile.NamedTemporaryFile(delete=False, suffix='.mp4')
                tfile.write(uploaded_file.read())
                st.session_state.videos.append({
                    'name': uploaded_file.name,
                    'path': tfile.name,
                    'size': uploaded_file.size / (1024*1024)  # MB
                })
            
            st.success(f"✅ {len(st.session_state.videos)} video(s) cargado(s)")
            
            # Mostrar tabla de videos
            df_videos = pd.DataFrame(st.session_state.videos)
            df_videos['size'] = df_videos['size'].apply(lambda x: f"{x:.2f} MB")
            st.dataframe(df_videos[['name', 'size']], use_container_width=True)
    
    with col2:
        st.metric("Videos Cargados", len(st.session_state.videos))
        st.metric("Duración Estimada", f"~{len(st.session_state.videos) * 10} min")
        st.metric("Intervalos de 15 min", f"~{len(st.session_state.videos) * 12}")
    
    st.markdown("---")
    
# ==================== CONFIGURACIÓN DE ZONAS Y LÍNEAS (ACTUALIZADO) ====================
st.header("2️⃣ Definir Zonas y Líneas de Conteo")

if st.session_state.videos:
    # Cargar primer frame del primer video
    if st.session_state.current_frame is None:
        cap = cv2.VideoCapture(st.session_state.videos[0]['path'])
        ret, frame = cap.read()
        cap.release()
        
        if ret:
            st.session_state.current_frame = frame
    
    if st.session_state.current_frame is not None:
        from drawing_tool import DrawingTool
        from line_detector import AutoLineDetector
        
        # Botón de detección automática
        col_auto1, col_auto2, col_auto3 = st.columns([2, 2, 1])
        
        with col_auto1:
            if st.button("🤖 Detectar Líneas Automáticamente", type="primary"):
                with st.spinner("Analizando estructura de la vía..."):
                    detector = AutoLineDetector(st.session_state.current_frame)
                    suggested_lines = detector.suggest_counting_lines(num_suggestions=4)
                    
                    # Agregar líneas sugeridas
                    st.session_state.lines.extend(suggested_lines)
                    
                    st.success(f"✅ {len(suggested_lines)} líneas detectadas automáticamente")
        
        with col_auto2:
            st.info("💡 La IA analizará la estructura de la vía y sugerirá líneas óptimas")
        
        with col_auto3:
            num_auto_lines = sum(1 for line in st.session_state.lines if line.get('auto_detected', False))
            st.metric("Líneas Auto", num_auto_lines)
        
        st.markdown("---")
        
        # Selector de herramienta
        tool_mode = st.radio(
            "🛠️ Selecciona Herramienta",
            ["📏 Líneas de Conteo", "🔷 Zonas Poligonales", "👁️ Vista Previa"],
            horizontal=True
        )
        
        st.markdown("---")
        
        if tool_mode == "📏 Líneas de Conteo":
            drawing_tool = DrawingTool(st.session_state.current_frame, canvas_key="lines_canvas")
            new_lines = drawing_tool.draw_lines([])
            
            # Agregar nuevas líneas sin duplicar
            for new_line in new_lines:
                if new_line not in st.session_state.lines:
                    st.session_state.lines.append(new_line)
            
            # Mostrar resumen
            if st.session_state.lines:
                with st.expander("📋 Líneas Configuradas", expanded=True):
                    for idx, line in enumerate(st.session_state.lines):
                        col1, col2, col3, col4 = st.columns([2, 2, 1, 1])
                        with col1:
                            st.write(f"**{line['name']}**")
                            # Mostrar coordenadas de la línea
                            try:
                                coords_txt = f"Coords: {line.get('coords')}"
                            except Exception:
                                coords_txt = "Coords: N/A"
                            st.write(coords_txt)
                        with col2:
                            st.write(f"Dirección: {line['direction']}")
                        with col3:
                            if line.get('auto_detected', False):
                                st.write("🤖 Auto")
                        with col4:
                            if st.button("🗑️", key=f"del_line_{idx}"):
                                st.session_state.lines.pop(idx)
                                st.rerun()
        
        elif tool_mode == "🔷 Zonas Poligonales":
            drawing_tool = DrawingTool(st.session_state.current_frame, canvas_key="zones_canvas")
            new_zones = drawing_tool.draw_polygons([])
            
            # Agregar nuevas zonas sin duplicar
            for new_zone in new_zones:
                if new_zone not in st.session_state.zones:
                    st.session_state.zones.append(new_zone)
            
            # Mostrar resumen
            if st.session_state.zones:
                with st.expander("📋 Zonas Configuradas", expanded=True):
                    for idx, zone in enumerate(st.session_state.zones):
                        col1, col2, col3 = st.columns([2, 2, 1])
                        with col1:
                            st.write(f"**{zone['name']}**")
                            # Mostrar coordenadas del polígono
                            try:
                                coords_txt = f"Coords: {zone.get('coords')}"
                            except Exception:
                                coords_txt = "Coords: N/A"
                            st.write(coords_txt)
                        with col2:
                            st.write(f"Tipo: {zone['type']}")
                        with col3:
                            if st.button("🗑️", key=f"del_zone_{idx}"):
                                st.session_state.zones.pop(idx)
                                st.rerun()
        
        elif tool_mode == "👁️ Vista Previa":
            st.subheader("Vista Previa de Configuración")
            
            # Visualizar todas las anotaciones
            annotated_frame = DrawingTool.visualize_annotations(
                st.session_state.current_frame,
                st.session_state.lines,
                st.session_state.zones
            )
            
            st.image(
                cv2.cvtColor(annotated_frame, cv2.COLOR_BGR2RGB),
                caption="Frame con Todas las Anotaciones",
                use_container_width=True
            )
            
            # Resumen de configuración
            col1, col2 = st.columns(2)
            with col1:
                st.metric("Total de Líneas", len(st.session_state.lines))
                if st.session_state.lines:
                    st.write("**Líneas:**")
                    for line in st.session_state.lines:
                        auto_tag = " 🤖" if line.get('auto_detected', False) else ""
                        st.write(f"- {line['name']} ({line['direction']}){auto_tag}")
            
            with col2:
                st.metric("Total de Zonas", len(st.session_state.zones))
                if st.session_state.zones:
                    st.write("**Zonas:**")
                    for zone in st.session_state.zones:
                        st.write(f"- {zone['name']} ({zone['type']})")
            
            # Botones de acción
            st.markdown("---")
            col1, col2, col3 = st.columns(3)
            
            with col1:
                if st.button("💾 Guardar Configuración", type="primary"):
                    config_name = f"config_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
                    filename = os.path.join(TEMPLATES_DIR, f"{config_name}.json")
                    DrawingTool.export_config(st.session_state.lines, 
                                             st.session_state.zones, 
                                             filename)
                    st.success(f"✅ Configuración guardada: {config_name}")
            
            with col2:
                if st.button("🗑️ Limpiar Todo"):
                    st.session_state.lines = []
                    st.session_state.zones = []
                    st.warning("⚠️ Todas las anotaciones han sido eliminadas")
                    st.rerun()
            
            with col3:
                if st.button("🔄 Recargar Frame"):
                    st.session_state.current_frame = None
                    st.rerun()

else:
    st.warning("⚠️ Primero sube al menos un video para configurar zonas y líneas")

st.header("⚡ Procesamiento de Videos")
    
    if not st.session_state.videos:
        st.warning("⚠️ Primero configura los videos en la pestaña anterior")
    elif len(st.session_state.lines) == 0 and len(st.session_state.zones) == 0:
        st.warning("⚠️ Define al menos una línea o zona de conteo")
    else:
        # Resumen de configuración
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Videos a Procesar", len(st.session_state.videos))
        with col2:
            st.metric("Líneas de Conteo", len(st.session_state.lines))
        with col3:
            st.metric("Zonas Definidas", len(st.session_state.zones))
        with col4:
            total_duration = len(st.session_state.videos) * 10  # Estimación
            st.metric("Duración Estimada", f"~{total_duration} min")
        
        st.markdown("---")
        
        # Configuración de procesamiento
        with st.expander("⚙️ Configuración Avanzada", expanded=False):
            col1, col2 = st.columns(2)
            
            with col1:
                process_every_n_frames = st.slider(
                    "Procesar cada N frames",
                    min_value=1,
                    max_value=10,
                    value=2,
                    help="Procesar cada N frames para acelerar (1 = todos los frames)"
                )
                
                show_preview = st.checkbox(
                    "Mostrar vista previa durante procesamiento",
                    value=False,
                    help="⚠️ Puede ralentizar el procesamiento"
                )
            
            with col2:
                start_time_input = st.time_input(
                    "Hora de inicio del primer video",
                    value=datetime.now().time(),
                    help="Hora real de inicio de la grabación"
                )
                
                save_annotated_video = st.checkbox(
                    "Guardar video con anotaciones",
                    value=False,
                    help="Genera un video con las detecciones dibujadas"
                )
        
        st.markdown("---")
        
        # Botón de inicio
        if st.button("🚀 INICIAR PROCESAMIENTO", type="primary", use_container_width=True):
            
            # Importar módulos necesarios
            from counter_v2 import CounterV2
            from datetime import datetime, timedelta
            import time
            
            # Contenedores de UI
            progress_bar = st.progress(0)
            status_text = st.empty()
            metrics_container = st.container()
            log_container = st.expander("📋 Log de Procesamiento", expanded=True)
            preview_container = st.empty() if show_preview else None
            
            # Métricas en tiempo real
            with metrics_container:
                metric_col1, metric_col2, metric_col3, metric_col4 = st.columns(4)
                metric_vehicles = metric_col1.empty()
                metric_pedestrians = metric_col2.empty()
                metric_fps = metric_col3.empty()
                metric_eta = metric_col4.empty()
            
            with log_container:
                st.text("🔧 Inicializando sistema de detección...")
                
                try:
                    # Inicializar componentes
                    detector = Detector(model_path=MODEL_PATH, device=DEVICE)
                    tracker = Tracker()
                    counter = CounterV2(
                        lines=st.session_state.lines,
                        zones=st.session_state.zones,
                        interval_minutes=15
                    )
                    
                    st.text("✅ Detector inicializado")
                    st.text("✅ Tracker inicializado")
                    st.text("✅ Counter inicializado")
                    st.text(f"✅ Configuración: {len(st.session_state.lines)} líneas, {len(st.session_state.zones)} zonas")
                    
                except Exception as e:
                    st.error(f"❌ Error al inicializar componentes: {str(e)}")
                    st.stop()
                
                st.markdown("---")
                
                # Variables de control
                total_vehicles = 0
                total_pedestrians = 0
                start_processing_time = time.time()
                
                # Configurar timestamp inicial
                base_date = datetime.now().date()
                video_start_time = datetime.combine(base_date, start_time_input)
                counter.set_start_time(video_start_time)
                
                # Procesar cada video
                for video_idx, video in enumerate(st.session_state.videos):
                    st.text(f"\n📹 Procesando video {video_idx + 1}/{len(st.session_state.videos)}: {video['name']}")
                    
                    try:
                        cap = cv2.VideoCapture(video['path'])
                        
                        if not cap.isOpened():
                            st.error(f"❌ No se pudo abrir el video: {video['name']}")
                            continue
                        
                        # Propiedades del video
                        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
                        fps = cap.get(cv2.CAP_PROP_FPS)
                        video_width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
                        video_height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
                        
                        st.text(f"   📊 Resolución: {video_width}x{video_height}")
                        st.text(f"   📊 FPS: {fps:.2f}")
                        st.text(f"   📊 Total frames: {total_frames}")
                        
                        # Configurar escritor de video si es necesario
                        video_writer = None
                        if save_annotated_video:
                            output_video_path = os.path.join(
                                OUTPUT_DIR,
                                f"annotated_{video['name']}"
                            )
                            fourcc = cv2.VideoWriter_fourcc(*'mp4v')
                            video_writer = cv2.VideoWriter(
                                output_video_path,
                                fourcc,
                                fps,
                                (video_width, video_height)
                            )
                        
                        frame_count = 0
                        processed_frames = 0
                        video_start = time.time()
                        
                        # Procesar frames
                        while cap.isOpened():
                            ret, frame = cap.read()
                            if not ret:
                                break
                            
                            frame_count += 1
                            
                            # Procesar solo cada N frames
                            if frame_count % process_every_n_frames != 0:
                                continue
                            
                            processed_frames += 1
                            
                            # Calcular timestamp del frame actual
                            seconds_elapsed = frame_count / fps
                            frame_timestamp = video_start_time + timedelta(seconds=seconds_elapsed)
                            
                            # DETECCIÓN
                            detections = detector.detect(frame)
                            
                            # TRACKING
                            tracks = tracker.update(detections, frame)
                            
                            # CONTEO
                            counter.count(tracks, frame_timestamp)
                            
                            # Actualizar contadores
                            current_counts = counter.get_current_counts()
                            
                            # Calcular totales
                            total_vehicles = 0
                            total_pedestrians = 0
                            
                            for line_name, intervals in current_counts['lines'].items():
                                for interval, counts in intervals.items():
                                    for vehicle_class, count in counts.items():
                                        if vehicle_class == 'Peatón':
                                            total_pedestrians += count
                                        else:
                                            total_vehicles += count
                            
                            # Visualizar (opcional)
                            if show_preview and preview_container:
                                from drawing_tool import DrawingTool
                                annotated_frame = DrawingTool.visualize_annotations(
                                    frame,
                                    st.session_state.lines,
                                    st.session_state.zones
                                )
                                
                                # Dibujar detecciones
                                for track in tracks:
                                    bbox = track['bbox']
                                    cv2.rectangle(
                                        annotated_frame,
                                        (bbox[0], bbox[1]),
                                        (bbox[2], bbox[3]),
                                        (0, 255, 0),
                                        2
                                    )
                                    cv2.putText(
                                        annotated_frame,
                                        f"{track['class']} #{track['id']}",
                                        (bbox[0], bbox[1] - 10),
                                        cv2.FONT_HERSHEY_SIMPLEX,
                                        0.5,
                                        (0, 255, 0),
                                        2
                                    )
                                
                                preview_container.image(
                                    cv2.cvtColor(annotated_frame, cv2.COLOR_BGR2RGB),
                                    caption=f"Frame {frame_count}/{total_frames}",
                                    use_container_width=True
                                )
                                
                                if save_annotated_video and video_writer:
                                    video_writer.write(annotated_frame)
                            
                            # Actualizar progreso
                            video_progress = frame_count / total_frames
                            total_progress = (video_idx + video_progress) / len(st.session_state.videos)
                            progress_bar.progress(total_progress)
                            
                            # Calcular FPS de procesamiento
                            elapsed = time.time() - video_start
                            processing_fps = processed_frames / elapsed if elapsed > 0 else 0
                            
                            # Calcular ETA
                            remaining_frames = total_frames - frame_count
                            remaining_videos = len(st.session_state.videos) - video_idx - 1
                            eta_seconds = (remaining_frames / processing_fps) if processing_fps > 0 else 0
                            eta_seconds += remaining_videos * (total_frames / processing_fps) if processing_fps > 0 else 0
                            
                            # Actualizar métricas cada 50 frames
                            if frame_count % 50 == 0:
                                metric_vehicles.metric("🚗 Vehículos", total_vehicles)
                                metric_pedestrians.metric("🚶 Peatones", total_pedestrians)
                                metric_fps.metric("⚡ FPS", f"{processing_fps:.1f}")
                                metric_eta.metric("⏱️ ETA", f"{int(eta_seconds)}s")
                                
                                status_text.text(
                                    f"Video {video_idx + 1}/{len(st.session_state.videos)} | "
                                    f"Frame {frame_count}/{total_frames} | "
                                    f"{processing_fps:.1f} FPS"
                                )
                        
                        # Cerrar video
                        cap.release()
                        if video_writer:
                            video_writer.release()
                            st.text(f"   💾 Video anotado guardado: {output_video_path}")
                        
                        st.text(f"   ✅ Video completado en {time.time() - video_start:.1f}s")
                        
                        # Actualizar timestamp para el siguiente video
                        video_duration_seconds = total_frames / fps
                        video_start_time += timedelta(seconds=video_duration_seconds)
                    
                    except Exception as e:
                        st.error(f"   ❌ Error procesando {video['name']}: {str(e)}")
                        continue
                
                # Finalizar procesamiento
                st.markdown("---")
                st.text("\n📊 Generando reportes finales...")
                
                try:
                    # Obtener resultados consolidados
                    results = counter.get_results()
                    
                    # Guardar en session_state
                    st.session_state.results = results
                    st.session_state.processing_complete = True
                    
                    # Exportar a JSON
                    json_path = os.path.join(
                        OUTPUT_DIR,
                        f"results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
                    )
                    counter.export_to_json(json_path)
                    st.text(f"💾 Resultados guardados en: {json_path}")
                    
                    # Resumen final
                    total_time = time.time() - start_processing_time
                    st.markdown("---")
                    st.success(f"✅ Procesamiento completado exitosamente en {total_time:.1f}s")
                    
                    # Mostrar resumen
                    summary = results['summary']
                    st.text(f"\n📈 RESUMEN FINAL:")
                    st.text(f"   🚗 Total Vehículos: {summary['total_vehicles']}")
                    st.text(f"   🚶 Total Peatones: {summary['total_pedestrians']}")
                    st.text(f"   ⏰ Hora Pico: {summary['peak_hour']} ({summary['peak_count']} vehículos)")
                    st.text(f"   ⚠️ Violaciones: {summary['total_violations']}")
                    
                    progress_bar.progress(1.0)
                    status_text.success("🎉 Procesamiento completado. Ve a la pestaña 'Resultados' para ver los reportes.")
                
                except Exception as e:
                    st.error(f"❌ Error al generar reportes: {str(e)}")
                    import traceback
                    st.code(traceback.format_exc())

st.header("📊 Resultados y Reportes")
    
    if not st.session_state.processing_complete:
        st.info("ℹ️ Los resultados aparecerán aquí después del procesamiento")
        st.markdown("---")
        
        # Mostrar ejemplo de lo que verá el usuario
        st.subheader("Vista Previa de Reportes")
        col1, col2 = st.columns(2)
        
        with col1:
            st.image("https://placehold.co/600x400/1f77b4/white?text=Graficos+Interactivos", 
                    caption="Gráficos de flujo vehicular")
        
        with col2:
            st.image("https://placehold.co/600x400/2ca02c/white?text=Dashboard+KPIs", 
                    caption="Indicadores clave de rendimiento")
        
        st.info("💡 **Tip:** Después del procesamiento podrás:\n"
               "- Ver gráficos interactivos de flujo vehicular\n"
               "- Analizar hora pico por dirección\n"
               "- Descargar Excel en formato MTC\n"
               "- Exportar reportes en PDF")
    
    else:
        # Obtener resultados
        results = st.session_state.results
        summary = results['summary']
        line_counts = results['line_counts']
        zone_counts = results['zone_counts']
        violations = results['violations']
        metadata = results['metadata']
        
        # ==================== SECCIÓN 1: KPIs PRINCIPALES ====================
        st.subheader("📈 Indicadores Clave de Rendimiento (KPIs)")
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.markdown('<div class="metric-card">', unsafe_allow_html=True)
            st.metric(
                "🚗 Total Vehículos",
                f"{summary['total_vehicles']:,}",
                help="Suma de todos los vehículos contados en todas las líneas"
            )
            st.markdown('</div>', unsafe_allow_html=True)
        
        with col2:
            st.markdown('<div class="metric-card">', unsafe_allow_html=True)
            st.metric(
                "🚶 Total Peatones",
                f"{summary['total_pedestrians']:,}",
                help="Suma de todos los peatones contados"
            )
            st.markdown('</div>', unsafe_allow_html=True)
        
        with col3:
            st.markdown('<div class="metric-card">', unsafe_allow_html=True)
            peak_hour_display = summary['peak_hour'] if summary['peak_hour'] else "N/A"
            st.metric(
                "⏰ Hora Pico",
                peak_hour_display,
                help="Hora con mayor volumen vehicular"
            )
            st.markdown('</div>', unsafe_allow_html=True)
        
        with col4:
            st.markdown('<div class="metric-card">', unsafe_allow_html=True)
            st.metric(
                "📊 Vehículos/Hora (Pico)",
                f"{summary['peak_count']:,}",
                help="Cantidad de vehículos en la hora pico"
            )
            st.markdown('</div>', unsafe_allow_html=True)
        
        # KPIs adicionales
        col5, col6, col7, col8 = st.columns(4)
        
        with col5:
            st.metric("📏 Líneas Configuradas", metadata['total_lines'])
        
        with col6:
            st.metric("🔷 Zonas Configuradas", metadata['total_zones'])
        
        with col7:
            st.metric("⚠️ Violaciones Detectadas", summary['total_violations'])
        
        with col8:
            total_count = summary['total_vehicles'] + summary['total_pedestrians']
            st.metric("📊 Total General", f"{total_count:,}")
        
        st.markdown("---")
        
        # ==================== SECCIÓN 2: GRÁFICOS INTERACTIVOS ====================
        st.subheader("📊 Análisis Visual de Flujo")
        
        # Preparar datos para gráficos
        def prepare_time_series_data(line_counts):
            """Prepara datos para gráfico de series de tiempo."""
            data = []
            
            for line in line_counts:
                line_name = line['name']
                direction = line['direction']
                
                for interval_data in line['intervals']:
                    time = interval_data['time']
                    counts = interval_data['counts']
                    
                    for vehicle_class, count in counts.items():
                        data.append({
                            'Línea': f"{line_name} ({direction})",
                            'Hora': time,
                            'Tipo': vehicle_class,
                            'Cantidad': count
                        })
            
            return pd.DataFrame(data)
        
        def prepare_vehicle_distribution(line_counts):
            """Prepara datos para distribución por tipo de vehículo."""
            vehicle_totals = defaultdict(int)
            
            for line in line_counts:
                for interval_data in line['intervals']:
                    for vehicle_class, count in interval_data['counts'].items():
                        vehicle_totals[vehicle_class] += count
            
            return pd.DataFrame([
                {'Tipo': k, 'Cantidad': v}
                for k, v in vehicle_totals.items()
            ])
        
        def prepare_direction_analysis(line_counts):
            """Prepara datos para análisis por dirección."""
            direction_totals = defaultdict(int)
            
            for line in line_counts:
                direction = line['direction']
                for interval_data in line['intervals']:
                    direction_totals[direction] += interval_data['total']
            
            return pd.DataFrame([
                {'Dirección': k, 'Total': v}
                for k, v in direction_totals.items()
            ])
        
        # Gráfico 1: Flujo por Intervalos de Tiempo
        if line_counts:
            col_left, col_right = st.columns(2)
            
            with col_left:
                st.markdown("#### 📈 Flujo Vehicular por Intervalos de 15 min")
                
                df_time_series = prepare_time_series_data(line_counts)
                
                if not df_time_series.empty:
                    # Agrupar por hora y línea
                    df_grouped = df_time_series.groupby(['Hora', 'Línea'])['Cantidad'].sum().reset_index()
                    
                    fig_time = px.line(
                        df_grouped,
                        x='Hora',
                        y='Cantidad',
                        color='Línea',
                        markers=True,
                        title="Evolución del Tráfico por Línea de Conteo",
                        labels={'Cantidad': 'Vehículos', 'Hora': 'Intervalo de Tiempo'}
                    )
                    
                    fig_time.update_layout(
                        hovermode='x unified',
                        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
                    )
                    
                    st.plotly_chart(fig_time, use_container_width=True)
                else:
                    st.warning("No hay datos de series de tiempo disponibles")
            
            with col_right:
                st.markdown("#### 🚗 Distribución por Tipo de Vehículo")
                
                df_vehicles = prepare_vehicle_distribution(line_counts)
                
                if not df_vehicles.empty:
                    fig_pie = px.pie(
                        df_vehicles,
                        values='Cantidad',
                        names='Tipo',
                        title="Composición del Tráfico",
                        hole=0.4,
                        color_discrete_sequence=px.colors.qualitative.Set3
                    )
                    
                    fig_pie.update_traces(textposition='inside', textinfo='percent+label')
                    
                    st.plotly_chart(fig_pie, use_container_width=True)
                else:
                    st.warning("No hay datos de distribución disponibles")
            
            # Gráfico 2: Análisis por Dirección
            st.markdown("#### 🧭 Volumen por Dirección de Flujo")
            
            df_directions = prepare_direction_analysis(line_counts)
            
            if not df_directions.empty:
                fig_directions = px.bar(
                    df_directions,
                    x='Dirección',
                    y='Total',
                    title="Comparación de Flujo por Dirección",
                    color='Total',
                    color_continuous_scale='Blues',
                    text='Total'
                )
                
                fig_directions.update_traces(texttemplate='%{text:,}', textposition='outside')
                fig_directions.update_layout(showlegend=False)
                
                st.plotly_chart(fig_directions, use_container_width=True)
            else:
                st.warning("No hay datos de dirección disponibles")
            
            # Gráfico 3: Mapa de Calor (Heatmap)
            st.markdown("#### 🔥 Mapa de Calor: Intensidad de Tráfico")
            
            df_time_series = prepare_time_series_data(line_counts)
            
            if not df_time_series.empty:
                # Crear pivot table para heatmap
                df_pivot = df_time_series.pivot_table(
                    index='Línea',
                    columns='Hora',
                    values='Cantidad',
                    aggfunc='sum',
                    fill_value=0
                )
                
                fig_heatmap = px.imshow(
                    df_pivot,
                    labels=dict(x="Hora", y="Línea de Conteo", color="Vehículos"),
                    title="Intensidad de Tráfico por Línea y Hora",
                    color_continuous_scale='RdYlGn_r',
                    aspect="auto"
                )
                
                fig_heatmap.update_xaxes(side="bottom")
                
                st.plotly_chart(fig_heatmap, use_container_width=True)
        
        st.markdown("---")
        
        # ==================== SECCIÓN 3: TABLAS DETALLADAS ====================
        st.subheader("📋 Datos Detallados")
        
        tab_lines, tab_zones, tab_violations, tab_peak = st.tabs([
            "📏 Conteo por Líneas",
            "🔷 Conteo por Zonas",
            "⚠️ Violaciones",
            "⏰ Análisis de Hora Pico"
        ])
        
        # TAB: Conteo por Líneas
        with tab_lines:
            if line_counts:
                for line in line_counts:
                    with st.expander(f"📏 {line['name']} - Dirección: {line['direction']}", expanded=False):
                        # Crear DataFrame
                        intervals_data = []
                        for interval in line['intervals']:
                            row = {'Hora': interval['time']}
                            row.update(interval['counts'])
                            row['Total'] = interval['total']
                            intervals_data.append(row)
                        
                        df_line = pd.DataFrame(intervals_data)
                        
                        if not df_line.empty:
                            # Mostrar tabla
                            st.dataframe(df_line, use_container_width=True)
                            
                            # Gráfico de barras apiladas
                            df_melted = df_line.melt(
                                id_vars=['Hora'],
                                value_vars=[col for col in df_line.columns if col not in ['Hora', 'Total']],
                                var_name='Tipo',
                                value_name='Cantidad'
                            )
                            
                            fig_stacked = px.bar(
                                df_melted,
                                x='Hora',
                                y='Cantidad',
                                color='Tipo',
                                title=f"Composición del Tráfico - {line['name']}",
                                barmode='stack'
                            )
                            
                            st.plotly_chart(fig_stacked, use_container_width=True)
                        else:
                            st.info("No hay datos para esta línea")
            else:
                st.info("No se configuraron líneas de conteo")
        
        # TAB: Conteo por Zonas
        with tab_zones:
            if zone_counts:
                for zone in zone_counts:
                    with st.expander(f"🔷 {zone['name']} - Tipo: {zone['type']}", expanded=False):
                        # Crear DataFrame
                        intervals_data = []
                        for interval in zone['intervals']:
                            row = {'Hora': interval['time']}
                            row.update(interval['counts'])
                            row['Total'] = interval['total']
                            intervals_data.append(row)
                        
                        df_zone = pd.DataFrame(intervals_data)
                        
                        if not df_zone.empty:
                            st.dataframe(df_zone, use_container_width=True)
                            
                            # Gráfico de línea
                            fig_zone = px.line(
                                df_zone,
                                x='Hora',
                                y='Total',
                                title=f"Actividad en Zona - {zone['name']}",
                                markers=True
                            )
                            
                            st.plotly_chart(fig_zone, use_container_width=True)
                        else:
                            st.info("No hay datos para esta zona")
            else:
                st.info("No se configuraron zonas de conteo")
        
        # TAB: Violaciones
        with tab_violations:
            if violations:
                st.warning(f"⚠️ Se detectaron {len(violations)} violaciones")
                
                df_violations = pd.DataFrame(violations)
                st.dataframe(df_violations, use_container_width=True)
                
                # Gráfico de violaciones por zona
                violations_by_zone = df_violations.groupby('zone').size().reset_index(name='Cantidad')
                
                fig_violations = px.bar(
                    violations_by_zone,
                    x='zone',
                    y='Cantidad',
                    title="Violaciones por Zona",
                    color='Cantidad',
                    color_continuous_scale='Reds'
                )
                
                st.plotly_chart(fig_violations, use_container_width=True)
            else:
                st.success("✅ No se detectaron violaciones")
        
        # TAB: Análisis de Hora Pico
        with tab_peak:
            st.markdown("### 🏆 Análisis Detallado de Hora Pico")
            
            if summary['peak_hour']:
                st.info(f"**Hora Pico Identificada:** {summary['peak_hour']} con {summary['peak_count']} vehículos")
                
                # Encontrar datos de la hora pico
                peak_data = []
                
                for line in line_counts:
                    for interval in line['intervals']:
                        if interval['time'] == summary['peak_hour']:
                            peak_data.append({
                                'Línea': line['name'],
                                'Dirección': line['direction'],
                                'Total': interval['total'],
                                **interval['counts']
                            })
                
                if peak_data:
                    df_peak = pd.DataFrame(peak_data)
                    
                    st.markdown("#### 📊 Distribución en Hora Pico por Línea")
                    st.dataframe(df_peak, use_container_width=True)
                    
                    # Gráfico de barras
                    fig_peak = px.bar(
                        df_peak,
                        x='Línea',
                        y='Total',
                        color='Dirección',
                        title=f"Volumen por Línea en Hora Pico ({summary['peak_hour']})",
                        text='Total'
                    )
                    
                    fig_peak.update_traces(texttemplate='%{text}', textposition='outside')
                    
                    st.plotly_chart(fig_peak, use_container_width=True)
                    
                    # Top 3 líneas más congestionadas
                    st.markdown("#### 🔝 Top 3 Líneas Más Congestionadas")
                    
                    df_peak_sorted = df_peak.sort_values('Total', ascending=False).head(3)
                    
                    for idx, row in df_peak_sorted.iterrows():
                        col1, col2, col3 = st.columns([2, 2, 1])
                        with col1:
                            st.write(f"**{row['Línea']}**")
                        with col2:
                            st.write(f"Dirección: {row['Dirección']}")
                        with col3:
                            st.metric("Vehículos", row['Total'])
            else:
                st.warning("No se pudo determinar la hora pico")
        
        st.markdown("---")
        
        # ==================== SECCIÓN 4: EXPORTACIÓN ====================
        st.subheader("💾 Exportar Resultados")
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.markdown("#### 📥 Excel MTC")
            
            if st.button("Generar Excel", type="primary", use_container_width=True):
                with st.spinner("Generando archivo Excel..."):
                    try:
                        from excel_generator import ExcelGenerator
                        
                        excel_gen = ExcelGenerator()
                        excel_filename = f"Aforo_MTC_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
                        excel_path = os.path.join(OUTPUT_DIR, excel_filename)
                        
                        # Generar Excel
                        excel_gen.generate(results, excel_path)
                        
                        # Botón de descarga
                        with open(excel_path, 'rb') as f:
                            st.download_button(
                                label="⬇️ Descargar Excel",
                                data=f,
                                file_name=excel_filename,
                                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                                use_container_width=True
                            )
                        
                        st.success("✅ Excel generado exitosamente")
                    
                    except Exception as e:
                        st.error(f"❌ Error al generar Excel: {str(e)}")
        
        with col2:
            st.markdown("#### 📄 JSON")
            
            json_data = json.dumps(results, indent=4, ensure_ascii=False)
            
            st.download_button(
                label="⬇️ Descargar JSON",
                data=json_data,
                file_name=f"results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
                mime="application/json",
                use_container_width=True
            )
        
        with col3:
            st.markdown("#### 📊 CSV")
            
            if st.button("Generar CSV", use_container_width=True):
                with st.spinner("Generando CSV..."):
                    try:
                        # Convertir a CSV
                        df_export = prepare_time_series_data(line_counts)
                        csv_data = df_export.to_csv(index=False)
                        
                        st.download_button(
                            label="⬇️ Descargar CSV",
                            data=csv_data,
                            file_name=f"aforo_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                            mime="text/csv",
                            use_container_width=True
                        )
                        
                        st.success("✅ CSV generado")
                    
                    except Exception as e:
                        st.error(f"❌ Error: {str(e)}")
        
        with col4:
            st.markdown("#### 📑 Reporte PDF")
            
            if st.button("Generar PDF", use_container_width=True):
                st.info("🚧 Funcionalidad en desarrollo")
        
        st.markdown("---")
        
        # ==================== SECCIÓN 5: METADATOS ====================
        with st.expander("ℹ️ Información del Procesamiento", expanded=False):
            col1, col2 = st.columns(2)
            
            with col1:
                st.markdown("**Configuración:**")
                st.write(f"- Hora de inicio: {metadata['start_time']}")
                st.write(f"- Intervalo: {metadata['interval_minutes']} minutos")
                st.write(f"- Líneas configuradas: {metadata['total_lines']}")
                st.write(f"- Zonas configuradas: {metadata['total_zones']}")
            
            with col2:
                st.markdown("**Resumen:**")
                st.write(f"- Total vehículos: {summary['total_vehicles']:,}")
                st.write(f"- Total peatones: {summary['total_pedestrians']:,}")
                st.write(f"- Hora pico: {summary['peak_hour']}")
                st.write(f"- Violaciones: {summary['total_violations']}")
        
        # Botón para reiniciar
        st.markdown("---")
        if st.button("🔄 Procesar Nuevos Videos", type="secondary"):
            st.session_state.processing_complete = False
            st.session_state.results = None
            st.session_state.videos = []
            st.session_state.lines = []
            st.session_state.zones = []
            st.rerun()

# ==================== FOOTER ====================
st.markdown("---")
st.markdown(
    """
    <div style='text-align: center; color: #666;'>
        <p>Sistema de Aforador Vehicular y Peatonal V2.0 | Desarrollado con ❤️ para Ingeniería de Tráfico</p>
        <p>Optimizado para AMD Ryzen 5 5600G | Compatible con GPU NVIDIA (próximamente)</p>
    </div>
    """,
    unsafe_allow_html=True
)