"""
theme.py - Sistema de diseño completo — Traffic Analysis Tool
Fase 1 completa: responsive, animaciones, componentes pulidos.
"""
# DESPUÉS
import streamlit as st
from typing import Union, Optional

COLORS = {
    "bg_primary":    "#0A0C10",
    "bg_surface":    "#111318",
    "bg_raised":     "#181C24",
    "bg_input":      "#161B26",
    "amber":         "#F5A623",
    "amber_dim":     "#6B4710",
    "amber_glow":    "rgba(245,166,35,0.10)",
    "amber_glow2":   "rgba(245,166,35,0.18)",
    "green":         "#22C55E",
    "green_dim":     "rgba(34,197,94,0.10)",
    "red":           "#EF4444",
    "red_dim":       "rgba(239,68,68,0.10)",
    "blue":          "#3B82F6",
    "blue_dim":      "rgba(59,130,246,0.10)",
    "text_primary":  "#F1F5F9",
    "text_secondary":"#94A3B8",
    "text_muted":    "#475569",
    "border":        "#1C2133",
    "border_mid":    "#263045",
    "border_bright": "#374F72",
    "car":     "#3B82F6",
    "moto":    "#F5A623",
    "bus":     "#22C55E",
    "truck":   "#EF4444",
    "person":  "#A78BFA",
    "bicycle": "#06B6D4",
    # NUEVOS COLORES
    "purple":        "#8B5CF6",
    "purple_dim":    "rgba(139,92,246,0.10)",
    "teal":          "#14B8A6",
    "teal_dim":      "rgba(20,184,166,0.10)",
    "rose":          "#F43F5E",
    "rose_dim":      "rgba(244,63,94,0.10)",
    "indigo":        "#6366F1",
    "indigo_dim":    "rgba(99,102,241,0.10)",
    
    # Variantes para estados
    "success":       "#22C55E",
    "warning":       "#F59E0B",
    "error":         "#EF4444",
    "info":          "#3B82F6",
    
    # Sombras
    "shadow_sm":     "0 1px 2px rgba(0,0,0,0.3)",
    "shadow_md":     "0 4px 12px rgba(0,0,0,0.4)",
    "shadow_lg":     "0 8px 32px rgba(0,0,0,0.5)",
    "shadow_glow":   "0 0 30px rgba(245,166,35,0.15)",
}

def _build_css():
    c = COLORS
    return """<style>
@import url('https://fonts.googleapis.com/css2?family=Sora:wght@300;400;500;600;700&family=JetBrains+Mono:wght@400;500&display=swap');
*,*::before,*::after{box-sizing:border-box;}
@keyframes fadeUp{from{opacity:0;transform:translateY(10px);}to{opacity:1;transform:translateY(0);}}
.stApp{background-color:""" + c['bg_primary'] + """;font-family:'Sora',sans-serif;color:""" + c['text_primary'] + """;}
#MainMenu,footer,header{visibility:hidden;}
.block-container{padding:1.75rem 2rem 3rem!important;max-width:1300px!important;}
.block-container>div>div{animation:fadeUp 0.3s ease both;}
[data-testid="stSidebar"]{background:""" + c['bg_surface'] + """!important;border-right:1px solid """ + c['border'] + """!important;}
[data-testid="stSidebar"]>div:first-child{padding:1.25rem 1rem 2rem;}
[data-testid="stTabs"] [role="tablist"]{background:""" + c['bg_raised'] + """;border-radius:10px;padding:4px;border:1px solid """ + c['border'] + """;gap:2px;flex-wrap:wrap;}
[data-testid="stTabs"] [role="tab"]{background:transparent;color:""" + c['text_muted'] + """;font-family:'Sora',sans-serif;font-size:0.82rem;font-weight:500;border-radius:7px;border:none;padding:8px 18px;transition:all 0.18s;white-space:nowrap;}
[data-testid="stTabs"] [role="tab"]:hover{color:""" + c['text_secondary'] + """;background:""" + c['border'] + """;}
[data-testid="stTabs"] [role="tab"][aria-selected="true"]{background:""" + c['amber'] + """;color:#000!important;font-weight:700;box-shadow:0 2px 8px rgba(245,166,35,0.3);}
[data-testid="stTabPanel"]{padding-top:1.5rem;}
.stButton>button{background:transparent;color:""" + c['text_secondary'] + """;border:1px solid """ + c['border_mid'] + """;border-radius:8px;font-family:'Sora',sans-serif;font-size:0.84rem;font-weight:500;padding:9px 18px;transition:all 0.18s;width:100%;}
.stButton>button:hover{border-color:""" + c['amber'] + """;color:""" + c['amber'] + """;background:""" + c['amber_glow'] + """;transform:translateY(-1px);}
.stButton>button:active{transform:translateY(0);}
.stButton>button[kind="primary"]{background:""" + c['amber'] + """;color:#000!important;border-color:""" + c['amber'] + """;font-weight:600;box-shadow:0 4px 14px rgba(245,166,35,0.25);}
.stButton>button[kind="primary"]:hover{background:#e89d1a;border-color:#e89d1a;box-shadow:0 6px 20px rgba(245,166,35,0.35);transform:translateY(-1px);}
.stTextInput>div>div>input,.stNumberInput>div>div>input{background:""" + c['bg_input'] + """!important;border:1px solid """ + c['border_mid'] + """!important;border-radius:8px!important;color:""" + c['text_primary'] + """!important;font-family:'JetBrains Mono',monospace!important;font-size:0.85rem!important;padding:9px 12px!important;transition:border-color 0.15s,box-shadow 0.15s!important;}
.stTextInput>div>div>input:focus,.stNumberInput>div>div>input:focus{border-color:""" + c['amber'] + """!important;box-shadow:0 0 0 3px """ + c['amber_glow2'] + """!important;}
.stTextInput label,.stNumberInput label{font-family:'Sora',sans-serif!important;font-size:0.75rem!important;font-weight:500!important;color:""" + c['text_secondary'] + """!important;}
[data-baseweb="select"]>div{background:""" + c['bg_input'] + """!important;border:1px solid """ + c['border_mid'] + """!important;border-radius:8px!important;color:""" + c['text_primary'] + """!important;font-family:'Sora',sans-serif!important;font-size:0.84rem!important;}
[data-baseweb="select"]>div:hover{border-color:""" + c['border_bright'] + """!important;}
[data-baseweb="menu"]{background:""" + c['bg_raised'] + """!important;border:1px solid """ + c['border_mid'] + """!important;border-radius:8px!important;}
[data-testid="stSlider"] [data-baseweb="slider"] [role="slider"]{background:""" + c['amber'] + """!important;border-color:""" + c['amber'] + """!important;box-shadow:0 0 0 4px """ + c['amber_glow2'] + """!important;}
[data-testid="stSlider"] [data-baseweb="slider"] [data-testid="stSliderTrack"]>div:nth-child(2){background:""" + c['amber'] + """!important;}
[data-testid="stSlider"] label{font-family:'Sora',sans-serif!important;font-size:0.75rem!important;color:""" + c['text_secondary'] + """!important;}
[data-testid="stMultiSelect"] [data-baseweb="select"]>div{background:""" + c['bg_input'] + """!important;border-color:""" + c['border_mid'] + """!important;}
[data-baseweb="tag"]{background:""" + c['amber_glow'] + """!important;border:1px solid """ + c['amber_dim'] + """!important;color:""" + c['amber'] + """!important;font-family:'Sora',sans-serif!important;font-size:0.74rem!important;border-radius:5px!important;}
[data-testid="stCheckbox"] label{color:""" + c['text_secondary'] + """!important;font-size:0.85rem!important;font-family:'Sora',sans-serif!important;}
[data-testid="stCheckbox"] svg{color:""" + c['amber'] + """!important;}
[data-testid="stFileUploadDropzone"]{background:""" + c['bg_raised'] + """!important;border:1.5px dashed """ + c['border_bright'] + """!important;border-radius:12px!important;transition:all 0.2s!important;}
[data-testid="stFileUploadDropzone"]:hover{border-color:""" + c['amber'] + """!important;background:""" + c['amber_glow'] + """!important;}
[data-testid="stFileUploadDropzone"] p,[data-testid="stFileUploadDropzone"] span{color:""" + c['text_muted'] + """!important;font-size:0.84rem!important;font-family:'Sora',sans-serif!important;}
[data-testid="stMetric"]{background:""" + c['bg_raised'] + """;border:1px solid """ + c['border'] + """;border-radius:10px;padding:16px 18px;transition:border-color 0.2s;}
[data-testid="stMetricLabel"] p{font-family:'Sora',sans-serif!important;font-size:0.7rem!important;font-weight:500!important;letter-spacing:0.07em!important;text-transform:uppercase!important;color:""" + c['text_muted'] + """!important;}
[data-testid="stMetricValue"]{font-family:'JetBrains Mono',monospace!important;font-size:1.45rem!important;font-weight:500!important;color:""" + c['text_primary'] + """!important;}
[data-testid="stDataFrame"]{background:""" + c['bg_surface'] + """;border:1px solid """ + c['border'] + """;border-radius:10px;overflow:hidden;}
[data-testid="stDataFrame"] th{background:""" + c['bg_raised'] + """!important;color:""" + c['text_muted'] + """!important;font-family:'Sora',sans-serif!important;font-size:0.7rem!important;font-weight:600!important;letter-spacing:0.08em!important;text-transform:uppercase!important;padding:10px 14px!important;border-bottom:1px solid """ + c['border_mid'] + """!important;}
[data-testid="stDataFrame"] td{color:""" + c['text_primary'] + """!important;font-family:'JetBrains Mono',monospace!important;font-size:0.82rem!important;padding:9px 14px!important;}
[data-testid="stAlert"]{border-radius:10px!important;font-family:'Sora',sans-serif!important;font-size:0.85rem!important;border-left-width:3px!important;}
div.stSuccess{background:""" + c['green_dim'] + """!important;border-color:""" + c['green'] + """!important;}
div.stWarning{background:""" + c['amber_glow'] + """!important;border-color:""" + c['amber'] + """!important;}
div.stError{background:""" + c['red_dim'] + """!important;border-color:""" + c['red'] + """!important;}
div.stInfo{background:""" + c['blue_dim'] + """!important;border-color:""" + c['blue'] + """!important;}
[data-testid="stExpander"]{background:""" + c['bg_surface'] + """!important;border:1px solid """ + c['border'] + """!important;border-radius:10px!important;}
[data-testid="stExpander"] summary{font-family:'Sora',sans-serif!important;font-size:0.84rem!important;font-weight:500!important;color:""" + c['text_secondary'] + """!important;padding:12px 16px!important;}
[data-testid="stExpander"] summary:hover{color:""" + c['text_primary'] + """!important;}
[data-testid="stProgressBar"]>div{background:""" + c['border'] + """!important;border-radius:100px!important;height:6px!important;overflow:hidden;}
[data-testid="stProgressBar"]>div>div{background:linear-gradient(90deg,""" + c['amber'] + """ 0%,#FFD166 100%)!important;border-radius:100px!important;transition:width 0.4s cubic-bezier(0.4,0,0.2,1)!important;box-shadow:0 0 8px rgba(245,166,35,0.4)!important;}
code{background:""" + c['bg_raised'] + """!important;border:1px solid """ + c['border'] + """!important;border-radius:5px!important;color:""" + c['amber'] + """!important;font-family:'JetBrains Mono',monospace!important;font-size:0.82rem!important;padding:2px 6px!important;}
[data-testid="stCaptionContainer"] p{color:""" + c['text_muted'] + """!important;font-size:0.77rem!important;font-family:'Sora',sans-serif!important;}
hr{border:none!important;border-top:1px solid """ + c['border'] + """!important;margin:1.5rem 0!important;}
::-webkit-scrollbar{width:5px;height:5px;}
::-webkit-scrollbar-track{background:""" + c['bg_primary'] + """;}
::-webkit-scrollbar-thumb{background:""" + c['border_bright'] + """;border-radius:3px;}
::-webkit-scrollbar-thumb:hover{background:""" + c['amber_dim'] + """;}
.tat-header{display:flex;align-items:center;gap:16px;padding:0 0 1.5rem;border-bottom:1px solid """ + c['border'] + """;margin-bottom:1.75rem;animation:fadeUp 0.4s ease both;}
.tat-header-icon{width:46px;height:46px;background:""" + c['amber'] + """;border-radius:12px;display:flex;align-items:center;justify-content:center;font-size:22px;flex-shrink:0;box-shadow:0 0 28px rgba(245,166,35,0.35);}
.tat-header-title{font-family:'Sora',sans-serif;font-size:1.4rem;font-weight:700;color:""" + c['text_primary'] + """;line-height:1;letter-spacing:-0.02em;}
.tat-header-sub{font-family:'Sora',sans-serif;font-size:0.77rem;color:""" + c['text_muted'] + """;margin-top:4px;}
.tat-header-badge{margin-left:auto;font-family:'JetBrains Mono',monospace;font-size:0.68rem;font-weight:500;color:""" + c['amber'] + """;background:""" + c['amber_glow'] + """;border:1px solid """ + c['amber_dim'] + """;border-radius:6px;padding:5px 11px;white-space:nowrap;flex-shrink:0;}
.tat-section{display:flex;align-items:center;gap:10px;font-family:'Sora',sans-serif;font-size:0.68rem;font-weight:600;letter-spacing:0.13em;text-transform:uppercase;color:""" + c['text_muted'] + """;padding-bottom:10px;border-bottom:1px solid """ + c['border'] + """;margin:1.25rem 0 1rem;}
.tat-section-bar{width:3px;height:13px;background:""" + c['amber'] + """;border-radius:2px;flex-shrink:0;}
.tat-sidebar-label{font-family:'Sora',sans-serif;font-size:0.64rem;font-weight:600;letter-spacing:0.14em;text-transform:uppercase;color:""" + c['text_muted'] + """;margin:0 0 8px;}
.tat-brand{display:flex;align-items:center;gap:10px;padding-bottom:16px;border-bottom:1px solid """ + c['border'] + """;margin-bottom:18px;}
.tat-brand-icon{width:36px;height:36px;background:""" + c['amber'] + """;border-radius:9px;display:flex;align-items:center;justify-content:center;font-size:18px;flex-shrink:0;box-shadow:0 0 18px rgba(245,166,35,0.3);}
.tat-brand-name{font-family:'Sora',sans-serif;font-size:0.9rem;font-weight:700;color:""" + c['text_primary'] + """;line-height:1;}
.tat-brand-ver{font-family:'JetBrains Mono',monospace;font-size:0.63rem;color:""" + c['text_muted'] + """;margin-top:3px;}
.tat-steps{padding:4px 0;}
.tat-step-row{display:flex;align-items:center;gap:10px;padding:6px 0;}
.tat-step-connector{width:1px;height:12px;background:""" + c['border_mid'] + """;margin-left:10px;}
.tat-step-num{width:22px;height:22px;border-radius:50%;background:""" + c['bg_raised'] + """;border:1px solid """ + c['border_mid'] + """;font-family:'JetBrains Mono',monospace;font-size:0.66rem;font-weight:500;color:""" + c['text_muted'] + """;display:flex;align-items:center;justify-content:center;flex-shrink:0;transition:all 0.2s;}
.tat-step-num.done{background:""" + c['green'] + """;border-color:""" + c['green'] + """;color:#000;font-weight:700;}
.tat-step-num.active{background:""" + c['amber'] + """;border-color:""" + c['amber'] + """;color:#000;font-weight:700;box-shadow:0 0 12px rgba(245,166,35,0.5);}
.tat-step-text{font-family:'Sora',sans-serif;font-size:0.79rem;color:""" + c['text_muted'] + """;transition:color 0.2s;}
.tat-step-text.active{color:""" + c['text_primary'] + """;font-weight:500;}
.tat-video-info{background:""" + c['bg_raised'] + """;border:1px solid """ + c['border'] + """;border-radius:10px;overflow:hidden;margin-bottom:10px;}
.tat-video-info-row{display:flex;justify-content:space-between;align-items:center;padding:8px 14px;border-bottom:1px solid """ + c['border'] + """;transition:background 0.15s;}
.tat-video-info-row:last-child{border-bottom:none;}
.tat-video-info-row:hover{background:rgba(255,255,255,0.02);}
.tat-vi-key{font-family:'Sora',sans-serif;font-size:0.71rem;color:""" + c['text_muted'] + """;}
.tat-vi-val{font-family:'JetBrains Mono',monospace;font-size:0.79rem;color:""" + c['text_primary'] + """;font-weight:500;}
.tat-metric{background:""" + c['bg_raised'] + """;border:1px solid """ + c['border'] + """;border-radius:10px;padding:15px 17px;position:relative;overflow:hidden;transition:border-color 0.2s,transform 0.15s;}
.tat-metric:hover{border-color:""" + c['border_bright'] + """;transform:translateY(-1px);}
.tat-metric::before{content:'';position:absolute;top:0;left:0;right:0;height:2px;border-radius:10px 10px 0 0;}
.tat-metric.car::before{background:""" + c['car'] + """;}
.tat-metric.moto::before{background:""" + c['moto'] + """;}
.tat-metric.bus::before{background:""" + c['bus'] + """;}
.tat-metric.truck::before{background:""" + c['truck'] + """;}
.tat-metric.person::before{background:""" + c['person'] + """;}
.tat-metric.bicycle::before{background:""" + c['bicycle'] + """;}
.tat-metric-label{font-family:'Sora',sans-serif;font-size:0.66rem;font-weight:600;letter-spacing:0.1em;text-transform:uppercase;color:""" + c['text_muted'] + """;margin-bottom:7px;}
.tat-metric-value{font-family:'JetBrains Mono',monospace;font-size:1.7rem;font-weight:500;color:""" + c['text_primary'] + """;line-height:1;}
.tat-metric-sub{font-family:'Sora',sans-serif;font-size:0.71rem;color:""" + c['text_muted'] + """;margin-top:6px;}
.tat-badge{display:inline-flex;align-items:center;gap:5px;font-family:'Sora',sans-serif;font-size:0.71rem;font-weight:600;letter-spacing:0.05em;text-transform:uppercase;border-radius:6px;padding:4px 10px;}
.tat-badge.ready{background:""" + c['green_dim'] + """;color:#4ade80;border:1px solid rgba(34,197,94,0.25);}
.tat-badge.pending{background:""" + c['amber_glow'] + """;color:""" + c['amber'] + """;border:1px solid rgba(245,166,35,0.25);}
.tat-badge.error{background:""" + c['red_dim'] + """;color:#f87171;border:1px solid rgba(239,68,68,0.25);}
.tat-badge.inactive{background:rgba(71,85,105,0.12);color:""" + c['text_muted'] + """;border:1px solid """ + c['border'] + """;}
.tat-empty{background:""" + c['bg_raised'] + """;border:1.5px dashed """ + c['border_mid'] + """;border-radius:14px;padding:44px 28px;text-align:center;}
.tat-empty-icon{font-size:2rem;opacity:0.35;display:block;margin-bottom:14px;}
.tat-empty-title{font-family:'Sora',sans-serif;font-size:0.88rem;font-weight:600;color:""" + c['text_secondary'] + """;margin-bottom:7px;}
.tat-empty-desc{font-family:'Sora',sans-serif;font-size:0.79rem;color:""" + c['text_muted'] + """;line-height:1.65;}
@media(max-width:768px){
  .block-container{padding:1rem!important;}
  .tat-header{flex-wrap:wrap;gap:10px;}
  .tat-header-badge{margin-left:0;width:100%;}
  .tat-header-title{font-size:1.15rem;}
  [data-testid="stTabs"] [role="tab"]{padding:7px 12px;font-size:0.78rem;}
  .tat-metric-value{font-size:1.4rem;}
}
@media(max-width:480px){
  .block-container{padding:0.75rem!important;}
  .tat-header-icon{width:36px;height:36px;font-size:16px;}
  .tat-header-title{font-size:0.98rem;}
  [data-testid="stTabs"] [role="tab"]{padding:6px 9px;font-size:0.72rem;}
  .tat-metric{padding:11px 13px;}
  .tat-metric-value{font-size:1.2rem;}
  .tat-empty{padding:28px 16px;}
}

@keyframes pulse {
    0%, 100% { opacity: 1; }
    50% { opacity: 0.5; }
}

@keyframes slideDown {
    from { opacity: 0; transform: translateY(-10px); }
    to { opacity: 1; transform: translateY(0); }
}

@keyframes shimmer {
    0% { background-position: -200% 0; }
    100% { background-position: 200% 0; }
}

/* Clases utilitarias de animación */
.animate-pulse { animation: pulse 2s ease-in-out infinite; }
.animate-slide { animation: slideDown 0.3s ease both; }
.animate-shimmer { 
    background: linear-gradient(90deg, transparent 0%, rgba(255,255,255,0.05) 50%, transparent 100%);
    background-size: 200% 100%;
    animation: shimmer 2s infinite;
}

@media(max-width: 1024px) {
    .block-container { padding: 1.25rem!important; }
    .tat-header-title { font-size: 1.2rem; }
    [data-testid="stMetricValue"] { font-size: 1.2rem; }
}

@media(max-width: 768px) {
    .block-container { padding: 0.75rem!important; }
    [data-testid="stTabs"] [role="tab"] { padding: 6px 12px; font-size: 0.72rem; }
    .tat-metric { padding: 12px; }
    .tat-metric-value { font-size: 1rem; }
}

@media(max-width: 480px) {
    .block-container { padding: 0.5rem!important; }
    [data-testid="stColumns"] { flex-direction: column!important; gap: 0.5rem!important; }
    .tat-header { flex-direction: column; text-align: center; }
    .tat-header-badge { width: 100%; text-align: center; }
}
</style>"""

def apply_theme():
    st.markdown(_build_css(), unsafe_allow_html=True)

def header(title, subtitle, badge="v1.0"):
    st.markdown(f"""<div class="tat-header">
        <div class="tat-header-icon">🚦</div>
        <div><div class="tat-header-title">{title}</div>
             <div class="tat-header-sub">{subtitle}</div></div>
        <span class="tat-header-badge">{badge}</span>
    </div>""", unsafe_allow_html=True)

def section_title(text):
    st.markdown(f'<div class="tat-section"><span class="tat-section-bar"></span>{text}</div>',
                unsafe_allow_html=True)

def sidebar_label(text):
    st.markdown(f'<p class="tat-sidebar-label">{text}</p>', unsafe_allow_html=True)

def sidebar_brand():
    st.markdown("""<div class="tat-brand">
        <div class="tat-brand-icon">🚦</div>
        <div><div class="tat-brand-name">Traffic Analysis</div>
             <div class="tat-brand-ver">Lima · YOLOv8 · v1.0</div></div>
    </div>""", unsafe_allow_html=True)

def status_badge(label, status="inactive"):
    dot = {"ready":"●","pending":"◌","error":"✕","inactive":"○"}
    st.markdown(f'<span class="tat-badge {status}">{dot.get(status,"○")} {label}</span>',
                unsafe_allow_html=True)

def metric_card(label: str, 
                value: Union[str, int, float],
                subtitle: str = "",
                vehicle_class: str = "",
                trend: Optional[float] = None,
                icon: str = "",
                size: str = "md"):
    """
    Tarjeta de métrica mejorada con tendencia e ícono.
    
    Args:
        label: Etiqueta de la métrica
        value: Valor principal
        subtitle: Texto secundario
        vehicle_class: Clase para color de borde
        trend: Valor de tendencia (positivo = sube, negativo = baja)
        icon: Emoji o ícono
        size: Tamaño ('sm', 'md', 'lg')
    """
    cls = f" {vehicle_class}" if vehicle_class else ""
    sub = f'<div class="tat-metric-sub">{subtitle}</div>' if subtitle else ""
    
    trend_html = ""
    if trend is not None:
        arrow = "↑" if trend > 0 else "↓"
        color = "#22C55E" if trend > 0 else "#EF4444"
        trend_html = f'<span style="color:{color};font-size:0.75rem;margin-left:8px;">{arrow} {abs(trend):.1%}</span>'
    
    icon_html = f'<span style="font-size:1.2rem;margin-right:8px;">{icon}</span>' if icon else ""
    
    size_class = {"sm": "0.9rem", "md": "1.7rem", "lg": "2.2rem"}.get(size, "1.7rem")
    
    st.markdown(f"""<div class="tat-metric{cls}">
        <div class="tat-metric-label">{label}</div>
        <div class="tat-metric-value" style="font-size:{size_class};">
            {icon_html}{value}{trend_html}
        </div>
        {sub}
    </div>""", unsafe_allow_html=True)

def video_info_card(props):
    dur = props.get('duration', 0)
    dur_str = (f"{int(dur//3600)}h {int((dur%3600)//60)}m"
               if dur >= 3600 else f"{int(dur//60)}m {int(dur%60)}s")
    rows = [
        ("Resolución", f"{props.get('width','—')} × {props.get('height','—')} px"),
        ("FPS",        f"{props.get('fps',0):.1f}"),
        ("Duración",   dur_str),
        ("Frames",     f"{props.get('frame_count',0):,}"),
    ]
    html = '<div class="tat-video-info">' + "".join(
        f'<div class="tat-video-info-row"><span class="tat-vi-key">{k}</span>'
        f'<span class="tat-vi-val">{v}</span></div>' for k,v in rows
    ) + '</div>'
    st.markdown(html, unsafe_allow_html=True)

def step_indicator(steps, current):
    items = []
    for i, step in enumerate(steps):
        if i < current:    cn,ct,num = "done",  "done",  "✓"
        elif i == current: cn,ct,num = "active","active",str(i+1)
        else:              cn,ct,num = "",      "",      str(i+1)
        items.append(f'<div class="tat-step-row">'
                     f'<span class="tat-step-num {cn}">{num}</span>'
                     f'<span class="tat-step-text {ct}">{step}</span></div>')
        if i < len(steps)-1:
            items.append('<div class="tat-step-connector"></div>')
    st.markdown(f'<div class="tat-steps">{"".join(items)}</div>',
                unsafe_allow_html=True)

def live_metrics_panel(counts, fps=0.0, elapsed=0.0):
    CM = {'Auto':('car','Auto'),'Moto':('moto','Moto'),'Bus':('bus','Bus'),
          'Camión':('truck','Camión'),'Peatón':('person','Peatón'),'Bicicleta':('bicycle','Bici')}
    total = sum(counts.values())
    cols  = st.columns(len(counts)+1)
    for i,(label,val) in enumerate(counts.items()):
        cls,disp = CM.get(label,('',label))
        pct = f"{val/total*100:.0f}%" if total>0 else "—"
        with cols[i]: metric_card(disp,val,subtitle=pct,vehicle_class=cls)
    with cols[-1]:
        m,s = int(elapsed//60),int(elapsed%60)
        metric_card("Total",total,subtitle=f"⚡ {fps:.1f} fps · {m}:{s:02d}")

def empty_state(icon, title, description):
    st.markdown(f"""<div class="tat-empty">
        <span class="tat-empty-icon">{icon}</span>
        <div class="tat-empty-title">{title}</div>
        <div class="tat-empty-desc">{description}</div>
    </div>""", unsafe_allow_html=True)

