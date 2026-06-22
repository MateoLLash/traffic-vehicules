"""
components.py - Componentes HTML/JS embebidos para Traffic Analysis Tool

Usa st.components.v1.html() para renderizar elementos que Streamlit
no puede construir nativamente: reproductor de video con controles,
panel de métricas animado, canvas de zonas OD (Fase 4).

Importar desde app.py:
    from components import video_player, metrics_live_panel, od_zone_canvas
"""

import streamlit as st
import streamlit.components.v1 as components
import pandas as pd
from theme import COLORS


# ─────────────────────────────────────────────
# REPRODUCTOR DE VIDEO MEJORADO
# ─────────────────────────────────────────────

def video_player(video_path: str, height: int = 400):
    """
    Reproductor HTML5 con controles nativos mejorados y soporte
    para el video procesado exportado.

    Args:
        video_path: Ruta local o URL al archivo de video
        height:     Alto del reproductor en px
    """
    c = COLORS
    html = f"""
    <style>
        @import url('https://fonts.googleapis.com/css2?family=IBM+Plex+Mono:wght@400;500&family=Barlow+Condensed:wght@600&display=swap');

        .vp-wrap {{
            background: {c['bg_surface']};
            border: 1px solid {c['border']};
            border-radius: 10px;
            overflow: hidden;
            font-family: 'Barlow Condensed', sans-serif;
        }}
        .vp-video {{
            width: 100%;
            height: {height}px;
            object-fit: contain;
            background: #000;
            display: block;
        }}
        .vp-controls {{
            background: {c['bg_raised']};
            padding: 10px 14px;
            display: flex;
            align-items: center;
            gap: 12px;
            border-top: 1px solid {c['border']};
        }}
        .vp-btn {{
            background: transparent;
            border: 1px solid {c['border_bright']};
            border-radius: 5px;
            color: {c['text_primary']};
            width: 34px;
            height: 30px;
            cursor: pointer;
            font-size: 13px;
            display: flex;
            align-items: center;
            justify-content: center;
            transition: all 0.15s;
            flex-shrink: 0;
        }}
        .vp-btn:hover {{
            border-color: {c['amber']};
            color: {c['amber']};
        }}
        .vp-seek {{
            flex: 1;
            height: 4px;
            -webkit-appearance: none;
            appearance: none;
            background: {c['border_bright']};
            border-radius: 2px;
            outline: none;
            cursor: pointer;
        }}
        .vp-seek::-webkit-slider-thumb {{
            -webkit-appearance: none;
            width: 12px;
            height: 12px;
            background: {c['amber']};
            border-radius: 50%;
            cursor: pointer;
        }}
        .vp-time {{
            font-family: 'IBM Plex Mono', monospace;
            font-size: 0.75rem;
            color: {c['text_secondary']};
            white-space: nowrap;
            min-width: 90px;
            text-align: right;
        }}
        .vp-zoom-wrap {{
            display: flex;
            align-items: center;
            gap: 6px;
            font-size: 0.72rem;
            color: {c['text_muted']};
        }}
        .vp-zoom-wrap input {{
            width: 60px;
            height: 4px;
            -webkit-appearance: none;
            appearance: none;
            background: {c['border_bright']};
            border-radius: 2px;
            outline: none;
            cursor: pointer;
        }}
        .vp-zoom-wrap input::-webkit-slider-thumb {{
            -webkit-appearance: none;
            width: 10px;
            height: 10px;
            background: {c['amber']};
            border-radius: 50%;
        }}
    </style>

    <div class="vp-wrap">
        <div style="overflow:hidden; position:relative;">
            <video class="vp-video" id="vpVid" preload="metadata">
                <source src="{video_path}">
                Tu navegador no soporta video HTML5.
            </video>
        </div>
        <div class="vp-controls">
            <button class="vp-btn" id="vpPlay" title="Play / Pause">▶</button>
            <button class="vp-btn" id="vpRewind" title="−10s">↩</button>
            <input class="vp-seek" type="range" id="vpSeek" min="0" step="0.1" value="0">
            <span class="vp-time" id="vpTime">0:00 / 0:00</span>
            <div class="vp-zoom-wrap">
                🔍
                <input type="range" id="vpZoom" min="1" max="3" step="0.1" value="1" title="Zoom">
            </div>
        </div>
    </div>

    <script>
        const vid    = document.getElementById('vpVid');
        const btnPlay= document.getElementById('vpPlay');
        const seek   = document.getElementById('vpSeek');
        const timeEl = document.getElementById('vpTime');
        const zoom   = document.getElementById('vpZoom');

        function fmt(s) {{
            const m = Math.floor(s/60), ss = Math.floor(s%60);
            return m + ':' + String(ss).padStart(2,'0');
        }}

        vid.addEventListener('loadedmetadata', () => {{
            seek.max = vid.duration;
            timeEl.textContent = '0:00 / ' + fmt(vid.duration);
        }});

        vid.addEventListener('timeupdate', () => {{
            seek.value = vid.currentTime;
            timeEl.textContent = fmt(vid.currentTime) + ' / ' + fmt(vid.duration);
        }});

        vid.addEventListener('play',  () => btnPlay.textContent = '⏸');
        vid.addEventListener('pause', () => btnPlay.textContent = '▶');
        vid.addEventListener('ended', () => btnPlay.textContent = '▶');

        btnPlay.addEventListener('click', () => {{
            vid.paused ? vid.play() : vid.pause();
        }});

        document.getElementById('vpRewind').addEventListener('click', () => {{
            vid.currentTime = Math.max(0, vid.currentTime - 10);
        }});

        seek.addEventListener('input', () => {{ vid.currentTime = seek.value; }});

        zoom.addEventListener('input', () => {{
            vid.style.transform = 'scale(' + zoom.value + ')';
            vid.style.transformOrigin = 'center center';
        }});
    </script>
    """
    components.html(html, height=height + 70, scrolling=False)


# ─────────────────────────────────────────────
# PANEL DE MÉTRICAS LIVE (animado)
# ─────────────────────────────────────────────

def metrics_live_panel(counts: dict, fps: float = 0.0, elapsed: float = 0.0):
    """
    Panel de métricas en tiempo real con animación de contadores.
    Se llama dentro del loop de procesamiento para actualizar los números.

    Args:
        counts:  {'Auto': 12, 'Moto': 5, 'Bus': 2, 'Camión': 1, 'Peatón': 8}
        fps:     FPS de procesamiento actual
        elapsed: Segundos transcurridos
    """
    c = COLORS
    CLASS_COLORS = {
        'Auto':      c['car'],
        'Moto':      c['moto'],
        'Bus':       c['bus'],
        'Camión':    c['red'],
        'Peatón':    '#A78BFA',
        'Bicicleta': '#06B6D4',
    }
    total = sum(counts.values())

    cards_html = ""
    for label, val in counts.items():
        color = CLASS_COLORS.get(label, c['border_bright'])
        pct = f"{val/total*100:.0f}%" if total > 0 else "0%"
        bar_w = f"{val/max(max(counts.values()),1)*100:.0f}%"
        cards_html += f"""
        <div style="
            background:{c['bg_surface']};
            border:1px solid {c['border']};
            border-top:2px solid {color};
            border-radius:8px;
            padding:12px 14px;
            min-width:110px;
        ">
            <p style="font-family:'Barlow Condensed',sans-serif;font-size:0.7rem;
                      font-weight:700;letter-spacing:0.1em;text-transform:uppercase;
                      color:{c['text_muted']};margin:0 0 4px 0;">{label}</p>
            <p style="font-family:'IBM Plex Mono',monospace;font-size:1.7rem;
                      font-weight:500;color:{c['text_primary']};line-height:1;margin:0;">{val:,}</p>
            <div style="margin-top:6px;height:3px;background:{c['border']};border-radius:2px;">
                <div style="width:{bar_w};height:100%;background:{color};
                             border-radius:2px;transition:width 0.4s ease;"></div>
            </div>
            <p style="font-family:'Barlow',sans-serif;font-size:0.72rem;
                      color:{c['text_muted']};margin:3px 0 0 0;">{pct} del total</p>
        </div>"""

    # Tarjeta de totales y FPS
    mins = int(elapsed // 60)
    secs = int(elapsed % 60)
    elapsed_str = f"{mins}:{str(secs).padStart if False else str(secs).zfill(2)}"

    cards_html += f"""
        <div style="
            background:{c['bg_raised']};
            border:1px solid {c['border_bright']};
            border-top:2px solid {c['amber']};
            border-radius:8px;
            padding:12px 14px;
            min-width:110px;
        ">
            <p style="font-family:'Barlow Condensed',sans-serif;font-size:0.7rem;
                      font-weight:700;letter-spacing:0.1em;text-transform:uppercase;
                      color:{c['text_muted']};margin:0 0 4px 0;">Total</p>
            <p style="font-family:'IBM Plex Mono',monospace;font-size:1.7rem;
                      font-weight:500;color:{c['amber']};line-height:1;margin:0;">{total:,}</p>
            <p style="font-family:'IBM Plex Mono',monospace;font-size:0.78rem;
                      color:{c['text_secondary']};margin:6px 0 0 0;">
                ⚡ {fps:.1f} fps · ⏱ {elapsed_str}
            </p>
        </div>"""

    html = f"""
    <style>
        @import url('https://fonts.googleapis.com/css2?family=IBM+Plex+Mono:wght@400;500&family=Barlow+Condensed:wght@700&family=Barlow:wght@400&display=swap');
        .mlp-wrap {{
            display: flex;
            gap: 10px;
            flex-wrap: wrap;
            padding: 4px 0;
        }}
    </style>
    <div class="mlp-wrap">{cards_html}</div>
    """
    components.html(html, height=130, scrolling=False)


# ─────────────────────────────────────────────
# SIDEBAR LOGO / BRANDING
# ─────────────────────────────────────────────

def sidebar_brand():
    """Logo y nombre — st.markdown puro, sin iframe, fondo transparente."""
    st.markdown("""
    <div class="tat-brand">
        <div class="tat-brand-icon">🚦</div>
        <div>
            <div class="tat-brand-name">Traffic Analysis</div>
            <div class="tat-brand-ver">Lima · YOLOv8 · v1.0</div>
        </div>
    </div>
    """, unsafe_allow_html=True)


# ─────────────────────────────────────────────
# EMPTY STATE (cuando no hay video cargado)
# ─────────────────────────────────────────────

def empty_state(icon: str, title: str, description: str):
    """Empty state — st.markdown puro, sin iframe, fondo transparente."""
    st.markdown(f"""
    <div class="tat-empty">
        <span class="tat-empty-icon">{icon}</span>
        <div class="tat-empty-title">{title}</div>
        <div class="tat-empty-desc">{description}</div>
    </div>
    """, unsafe_allow_html=True)

def interactive_table(data: pd.DataFrame, 
                      title: str = "",
                      searchable: bool = True,
                      max_rows: int = 50,
                      height: int = 400):
    """
    Tabla interactiva con búsqueda y paginación (usando JS).
    """
    html = f"""
    <style>
        .it-wrap {{
            background: {COLORS['bg_surface']};
            border: 1px solid {COLORS['border']};
            border-radius: 10px;
            overflow: hidden;
            font-family: 'Sora', sans-serif;
        }}
        .it-header {{
            padding: 12px 16px;
            border-bottom: 1px solid {COLORS['border']};
            display: flex;
            justify-content: space-between;
            align-items: center;
            flex-wrap: wrap;
            gap: 10px;
        }}
        .it-title {{
            font-weight: 600;
            color: {COLORS['text_primary']};
            font-size: 0.9rem;
        }}
        .it-search {{
            background: {COLORS['bg_input']};
            border: 1px solid {COLORS['border_mid']};
            border-radius: 6px;
            padding: 6px 12px;
            color: {COLORS['text_primary']};
            font-size: 0.8rem;
            width: 200px;
        }}
        .it-search:focus {{
            border-color: {COLORS['amber']};
            outline: none;
        }}
        .it-table-wrap {{
            overflow: auto;
            max-height: {height}px;
        }}
        .it-table {{
            width: 100%;
            border-collapse: collapse;
            font-size: 0.8rem;
        }}
        .it-table th {{
            background: {COLORS['bg_raised']};
            color: {COLORS['text_muted']};
            font-weight: 600;
            text-transform: uppercase;
            font-size: 0.65rem;
            letter-spacing: 0.08em;
            padding: 10px 14px;
            text-align: left;
            border-bottom: 1px solid {COLORS['border_mid']};
            position: sticky;
            top: 0;
            z-index: 10;
        }}
        .it-table td {{
            padding: 8px 14px;
            color: {COLORS['text_secondary']};
            border-bottom: 1px solid {COLORS['border']};
        }}
        .it-table tr:hover td {{
            background: rgba(255,255,255,0.02);
        }}
        .it-footer {{
            padding: 8px 16px;
            border-top: 1px solid {COLORS['border']};
            color: {COLORS['text_muted']};
            font-size: 0.7rem;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }}
        .it-pagination {{
            display: flex;
            gap: 4px;
        }}
        .it-page-btn {{
            background: transparent;
            border: 1px solid {COLORS['border_mid']};
            border-radius: 4px;
            color: {COLORS['text_secondary']};
            padding: 2px 10px;
            cursor: pointer;
            font-size: 0.7rem;
        }}
        .it-page-btn:hover {{
            border-color: {COLORS['amber']};
            color: {COLORS['amber']};
        }}
        .it-page-btn.active {{
            background: {COLORS['amber']};
            border-color: {COLORS['amber']};
            color: #000;
        }}
    </style>
    <div class="it-wrap">
        <div class="it-header">
            <span class="it-title">{title}</span>
            <input class="it-search" type="text" placeholder="🔍 Buscar..." 
                   oninput="filterTable(this.value)">
        </div>
        <div class="it-table-wrap">
            <table class="it-table" id="interactiveTable">
                <thead>
                    <tr>{"".join(f'<th>{col}</th>' for col in data.columns)}</tr>
                </thead>
                <tbody>
                    {"".join(f'<tr>{"".join(f"<td>{val}</td>" for val in row)}</tr>' 
                              for row in data.values[:max_rows])}
                </tbody>
            </table>
        </div>
        <div class="it-footer">
            <span>Mostrando {min(max_rows, len(data))} de {len(data)} registros</span>
            <div class="it-pagination">
                <button class="it-page-btn" onclick="prevPage()">◀</button>
                <button class="it-page-btn active">1</button>
                <button class="it-page-btn" onclick="nextPage()">▶</button>
            </div>
        </div>
    </div>
    <script>
        function filterTable(query) {{
            const rows = document.querySelectorAll('#interactiveTable tbody tr');
            rows.forEach(row => {{
                const text = row.textContent.toLowerCase();
                row.style.display = text.includes(query.toLowerCase()) ? '' : 'none';
            }});
        }}
        function nextPage() {{ /* Implementar paginación */ }}
        function prevPage() {{ /* Implementar paginación */ }}
    </script>
    """
    components.html(html, height=height + 150, scrolling=False)

def toast_notification(message: str, 
                       type: str = "info",  # info, success, warning, error
                       duration: int = 3000):
    """
    Notificación tipo toast que aparece en la esquina.
    """
    colors = {
        "info": COLORS['blue'],
        "success": COLORS['green'],
        "warning": COLORS['amber'],
        "error": COLORS['red']
    }
    
    html = f"""
    <style>
        .toast-container {{
            position: fixed;
            top: 20px;
            right: 20px;
            z-index: 9999;
            animation: slideDown 0.3s ease both;
        }}
        .toast {{
            background: {COLORS['bg_raised']};
            border-left: 4px solid {colors.get(type, COLORS['info'])};
            border-radius: 8px;
            padding: 14px 20px;
            box-shadow: 0 8px 32px rgba(0,0,0,0.5);
            color: {COLORS['text_primary']};
            font-family: 'Sora', sans-serif;
            font-size: 0.85rem;
            min-width: 200px;
            max-width: 400px;
        }}
        .toast-close {{
            float: right;
            background: none;
            border: none;
            color: {COLORS['text_muted']};
            cursor: pointer;
            font-size: 1.1rem;
            margin-left: 12px;
        }}
    </style>
    <div class="toast-container" id="toast">
        <div class="toast">
            <button class="toast-close" onclick="this.parentElement.parentElement.remove()">✕</button>
            {message}
        </div>
    </div>
    <script>
        setTimeout(() => {{
            const el = document.getElementById('toast');
            if (el) el.style.opacity = '0';
            setTimeout(() => {{ if (el) el.remove(); }}, 300);
        }}, {duration});
    </script>
    """
    components.html(html, height=80, scrolling=False)

# ─────────────────────────────────────────────
# PANEL DE LÍNEAS DEFINIDAS (rediseñado)
# ─────────────────────────────────────────────

def lines_panel(lines: list):
    """
    Panel visual animado de líneas de conteo definidas.

    Args:
        lines: Lista de dicts con keys:
               'name' (str), 'direction' (str), 'color' (str hex),
               'start' (tuple x,y), 'end' (tuple x,y)
    """
    c = COLORS

    # Paleta de direcciones
    dir_styles = {
        'N-S': ('⬇', '#22c55e', 'rgba(34,197,94,0.15)'),
        'S-N': ('⬆', '#f59e0b', 'rgba(245,158,11,0.15)'),
        'E-O': ('➡', '#3b82f6', 'rgba(59,130,246,0.15)'),
        'O-E': ('⬅', '#a78bfa', 'rgba(167,139,250,0.15)'),
    }

    count = len(lines)

    if count == 0:
        empty_html = f"""
        <div style="
            background: {c['bg_surface']};
            border: 1px solid {c['border']};
            border-radius: 10px;
            padding: 24px 16px;
            text-align: center;
            font-family: 'Sora', sans-serif;
        ">
            <div style="font-size: 2rem; opacity: 0.3; margin-bottom: 8px;">╌</div>
            <p style="color: {c['text_muted']}; font-size: 0.78rem; margin: 0;">
                Sin líneas definidas.<br>
                Dibuja al menos una para continuar.
            </p>
        </div>
        """
        components.html(empty_html, height=130, scrolling=False)
        return

    cards_html = ""
    for i, line in enumerate(lines):
        name      = line.get('name', f'Línea_{i}')
        direction = line.get('direction', 'N-S')
        color_hex = line.get('color', '#22c55e')
        start     = line.get('start', (0, 0))
        end       = line.get('end', (0, 0))

        arrow, dir_color, dir_bg = dir_styles.get(direction, ('→', '#888', 'rgba(136,136,136,0.15)'))
        delay = i * 0.1

        cards_html += f"""
        <div style="
            background: {c['bg_surface']};
            border: 1px solid {c['border']};
            border-left: 3px solid {color_hex};
            border-radius: 10px;
            padding: 10px 12px;
            margin-bottom: 8px;
            animation: slideIn 0.3s ease {delay}s both;
            font-family: 'Sora', sans-serif;
        ">
            <!-- Nombre + ícono color -->
            <div style="display:flex; align-items:center; justify-content:space-between; margin-bottom:6px;">
                <div style="display:flex; align-items:center; gap:7px;">
                    <div style="width:9px;height:9px;border-radius:50%;background:{color_hex};flex-shrink:0;"></div>
                    <span style="font-size:0.8rem; font-weight:600; color:{c['text_primary']};">{name}</span>
                </div>
                <!-- Badge dirección -->
                <span style="
                    background:{dir_bg};
                    color:{dir_color};
                    font-size:0.68rem;
                    font-weight:600;
                    padding:2px 8px;
                    border-radius:20px;
                    letter-spacing:0.04em;
                ">{arrow} {direction}</span>
            </div>
            <!-- Coordenadas -->
            <div style="
                background: rgba(0,0,0,0.2);
                border-radius: 6px;
                padding: 6px 10px;
                display: flex;
                justify-content: space-between;
                align-items: center;
            ">
                <div>
                    <div style="font-size:0.6rem;color:{c['text_muted']};text-transform:uppercase;letter-spacing:0.05em;">inicio</div>
                    <div style="font-size:0.72rem;font-family:'IBM Plex Mono',monospace;color:{c['text_secondary']};">{start[0]}, {start[1]}</div>
                </div>
                <div style="color:{c['text_muted']};font-size:0.8rem;">→</div>
                <div style="text-align:right;">
                    <div style="font-size:0.6rem;color:{c['text_muted']};text-transform:uppercase;letter-spacing:0.05em;">fin</div>
                    <div style="font-size:0.72rem;font-family:'IBM Plex Mono',monospace;color:{c['text_secondary']};">{end[0]}, {end[1]}</div>
                </div>
            </div>
        </div>
        """

    panel_height = 60 + count * 110

    html = f"""
    <style>
        @import url('https://fonts.googleapis.com/css2?family=IBM+Plex+Mono:wght@400;500&family=Sora:wght@400;600&display=swap');
        @keyframes slideIn {{
            from {{ opacity: 0; transform: translateX(12px); }}
            to   {{ opacity: 1; transform: translateX(0); }}
        }}
    </style>

    <!-- Header del panel -->
    <div style="
        display: flex;
        align-items: center;
        justify-content: space-between;
        margin-bottom: 10px;
        padding-bottom: 8px;
        border-bottom: 1px solid {c['border']};
        font-family: 'Sora', sans-serif;
    ">
        <span style="font-size:0.68rem; font-weight:600; letter-spacing:0.1em;
                     text-transform:uppercase; color:{c['text_muted']};">
            Líneas definidas
        </span>
        <span style="
            background: {c['amber']};
            color: #000;
            font-size: 0.68rem;
            font-weight: 700;
            padding: 2px 8px;
            border-radius: 20px;
        ">{count}</span>
    </div>

    {cards_html}
    """

    components.html(html, height=panel_height, scrolling=False)