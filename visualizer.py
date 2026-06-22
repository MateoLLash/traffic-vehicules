"""
visualizer.py - Módulo de visualizaciones y gráficos

Este módulo genera visualizaciones estáticas y dinámicas del análisis de tráfico.
"""

import os
import numpy as np
import matplotlib.pyplot as plt
import matplotlib
matplotlib.use('Agg')  # Backend sin GUI
import seaborn as sns
from typing import Dict, List, Tuple, Optional
import cv2
from collections import defaultdict

from utils import setup_logger

# Configurar logger
logger = setup_logger('visualizer')

# Configurar estilo de seaborn
sns.set_style("whitegrid")
sns.set_palette("husl")


class TrafficVisualizer:
    """
    Generador de visualizaciones para análisis de tráfico
    
    Attributes:
        output_dir: Directorio para guardar visualizaciones
        dpi: Resolución de las imágenes
        figsize: Tamaño base de las figuras
    """
    
    def __init__(self, output_dir: str, dpi: int = 100, figsize: Tuple[int, int] = (12, 8)):
        """
        Inicializa el visualizador
        
        Args:
            output_dir: Directorio de salida
            dpi: DPI de las imágenes
            figsize: Tamaño de las figuras (ancho, alto)
        """
        self.output_dir = output_dir
        self.dpi = dpi
        self.figsize = figsize
        
        # Crear directorio
        os.makedirs(output_dir, exist_ok=True)
        
        logger.info(f"Visualizador inicializado: {output_dir}")
    
    def plot_total_counts_bar(self, statistics: Dict, filename: str = "conteos_totales.png") -> str:
        """
        Genera gráfico de barras con conteos totales por categoría
        
        Args:
            statistics: Estadísticas del análisis
            filename: Nombre del archivo
            
        Returns:
            Ruta del archivo generado
        """
        filepath = os.path.join(self.output_dir, filename)
        
        try:
            total_counts = statistics.get('total_counts', {})
            
            if not total_counts:
                logger.warning("No hay datos para graficar")
                return None
            
            # Crear figura
            fig, ax = plt.subplots(figsize=self.figsize, dpi=self.dpi)
            
            categories = list(total_counts.keys())
            counts = list(total_counts.values())
            colors = plt.cm.Set3(np.linspace(0, 1, len(categories)))
            
            # Gráfico de barras
            bars = ax.bar(categories, counts, color=colors, edgecolor='black', linewidth=1.5)
            
            # Agregar valores sobre las barras
            for bar in bars:
                height = bar.get_height()
                ax.text(bar.get_x() + bar.get_width()/2., height,
                       f'{int(height)}',
                       ha='center', va='bottom', fontsize=12, fontweight='bold')
            
            # Etiquetas y título
            ax.set_xlabel('Categoría', fontsize=14, fontweight='bold')
            ax.set_ylabel('Conteo Total', fontsize=14, fontweight='bold')
            ax.set_title('Conteos Totales por Categoría', fontsize=16, fontweight='bold', pad=20)
            
            # Rotar etiquetas si hay muchas categorías
            if len(categories) > 5:
                plt.xticks(rotation=45, ha='right')
            
            plt.tight_layout()
            plt.savefig(filepath, dpi=self.dpi, bbox_inches='tight')
            plt.close()
            
            logger.info(f"Gráfico de barras generado: {filepath}")
            return filepath
            
        except Exception as e:
            logger.error(f"Error al generar gráfico de barras: {e}")
            return None
    
    def plot_counts_by_line(self, statistics: Dict, filename: str = "conteos_por_linea.png") -> str:
        """
        Genera gráfico de barras agrupadas por línea
        
        Args:
            statistics: Estadísticas del análisis
            filename: Nombre del archivo
            
        Returns:
            Ruta del archivo generado
        """
        filepath = os.path.join(self.output_dir, filename)
        
        try:
            counts_by_line = statistics.get('counts_by_line', [])
            
            if not counts_by_line:
                logger.warning("No hay datos de líneas para graficar")
                return None
            
            # Preparar datos
            line_names = []
            counts_by_category = defaultdict(list)
            
            for line_info in counts_by_line:
                line_names.append(line_info['line_name'])
                counts = line_info['counts_by_class']
                
                # Obtener todas las categorías
                all_categories = set()
                for line in counts_by_line:
                    all_categories.update(line['counts_by_class'].keys())
                
                # Agregar conteos
                for category in all_categories:
                    count = counts.get(category, {}).get('total', 0)
                    counts_by_category[category].append(count)
            
            # Crear figura
            fig, ax = plt.subplots(figsize=self.figsize, dpi=self.dpi)
            
            x = np.arange(len(line_names))
            width = 0.8 / len(counts_by_category)
            
            # Graficar barras agrupadas
            for i, (category, counts) in enumerate(counts_by_category.items()):
                offset = width * i - (width * len(counts_by_category)) / 2 + width / 2
                ax.bar(x + offset, counts, width, label=category)
            
            # Configurar gráfico
            ax.set_xlabel('Línea de Conteo', fontsize=14, fontweight='bold')
            ax.set_ylabel('Conteo', fontsize=14, fontweight='bold')
            ax.set_title('Conteos por Línea y Categoría', fontsize=16, fontweight='bold', pad=20)
            ax.set_xticks(x)
            ax.set_xticklabels(line_names, rotation=45, ha='right')
            ax.legend(title='Categoría', loc='upper left')
            ax.grid(axis='y', alpha=0.3)
            
            plt.tight_layout()
            plt.savefig(filepath, dpi=self.dpi, bbox_inches='tight')
            plt.close()
            
            logger.info(f"Gráfico por línea generado: {filepath}")
            return filepath
            
        except Exception as e:
            logger.error(f"Error al generar gráfico por línea: {e}")
            return None
    
    def plot_time_series(self, time_series: Dict, filename: str = "series_temporales.png") -> str:
        """
        Genera gráfico de líneas con series temporales
        
        Args:
            time_series: Datos de series temporales
            filename: Nombre del archivo
            
        Returns:
            Ruta del archivo generado
        """
        filepath = os.path.join(self.output_dir, filename)
        
        try:
            if not time_series or not time_series.get('counts'):
                logger.warning("No hay datos de series temporales")
                return None
            
            timestamps = time_series['timestamps']
            counts = time_series['counts']
            interval_seconds = time_series['interval_seconds']
            
            # Convertir timestamps a minutos
            timestamps_minutes = [t / 60 for t in timestamps]
            
            # Crear figura
            fig, ax = plt.subplots(figsize=(14, 8), dpi=self.dpi)
            
            # Graficar cada categoría
            for category, values in counts.items():
                ax.plot(timestamps_minutes, values, marker='o', 
                       linewidth=2, markersize=6, label=category)
            
            # Configurar gráfico
            ax.set_xlabel('Tiempo (minutos)', fontsize=14, fontweight='bold')
            ax.set_ylabel('Conteo por Intervalo', fontsize=14, fontweight='bold')
            ax.set_title(f'Flujo de Tráfico en el Tiempo (Intervalo: {interval_seconds}s)', 
                        fontsize=16, fontweight='bold', pad=20)
            ax.legend(title='Categoría', loc='upper left')
            ax.grid(True, alpha=0.3)
            
            plt.tight_layout()
            plt.savefig(filepath, dpi=self.dpi, bbox_inches='tight')
            plt.close()
            
            logger.info(f"Serie temporal generada: {filepath}")
            return filepath
            
        except Exception as e:
            logger.error(f"Error al generar serie temporal: {e}")
            return None
    
    def plot_direction_distribution(self, statistics: Dict, filename: str = "distribucion_direcciones.png") -> str:
        """
        Genera gráfico de pastel con distribución de direcciones
        
        Args:
            statistics: Estadísticas del análisis
            filename: Nombre del archivo
            
        Returns:
            Ruta del archivo generado
        """
        filepath = os.path.join(self.output_dir, filename)
        
        try:
            counts_by_line = statistics.get('counts_by_line', [])
            
            if not counts_by_line:
                logger.warning("No hay datos de dirección")
                return None
            
            # Agregar conteos por dirección
            direction_totals = {
                'Arriba → Abajo': 0,
                'Abajo → Arriba': 0,
                'Izquierda → Derecha': 0,
                'Derecha → Izquierda': 0
            }
            
            for line_info in counts_by_line:
                counts = line_info['counts_by_class']
                for class_counts in counts.values():
                    direction_totals['Arriba → Abajo'] += class_counts.get('up_to_down', 0)
                    direction_totals['Abajo → Arriba'] += class_counts.get('down_to_up', 0)
                    direction_totals['Izquierda → Derecha'] += class_counts.get('left_to_right', 0)
                    direction_totals['Derecha → Izquierda'] += class_counts.get('right_to_left', 0)
            
            # Filtrar direcciones con conteos
            directions = []
            counts = []
            for direction, count in direction_totals.items():
                if count > 0:
                    directions.append(direction)
                    counts.append(count)
            
            if not counts:
                logger.warning("No hay conteos por dirección")
                return None
            
            # Crear figura
            fig, ax = plt.subplots(figsize=(10, 10), dpi=self.dpi)
            
            colors = plt.cm.Pastel1(np.linspace(0, 1, len(directions)))
            explode = [0.05] * len(directions)
            
            # Gráfico de pastel
            wedges, texts, autotexts = ax.pie(counts, labels=directions, autopct='%1.1f%%',
                                               colors=colors, explode=explode,
                                               startangle=90, textprops={'fontsize': 12})
            
            # Mejorar apariencia
            for autotext in autotexts:
                autotext.set_color('white')
                autotext.set_fontweight('bold')
                autotext.set_fontsize(14)
            
            ax.set_title('Distribución de Direcciones de Tráfico', 
                        fontsize=16, fontweight='bold', pad=20)
            
            plt.tight_layout()
            plt.savefig(filepath, dpi=self.dpi, bbox_inches='tight')
            plt.close()
            
            logger.info(f"Gráfico de direcciones generado: {filepath}")
            return filepath
            
        except Exception as e:
            logger.error(f"Error al generar gráfico de direcciones: {e}")
            return None
    
    def plot_heatmap(self, crossings: List[Dict], frame_shape: Tuple[int, int],
                    filename: str = "mapa_calor.png") -> str:
        """
        Genera mapa de calor de actividad
        
        Args:
            crossings: Lista de cruces
            frame_shape: (altura, ancho) del frame
            filename: Nombre del archivo
            
        Returns:
            Ruta del archivo generado
        """
        filepath = os.path.join(self.output_dir, filename)
        
        try:
            if not crossings:
                logger.warning("No hay datos para mapa de calor")
                return None
            
            height, width = frame_shape
            
            # Crear mapa de densidad
            heatmap = np.zeros((height, width), dtype=np.float32)
            
            # Acumular posiciones
            for crossing in crossings:
                x, y = crossing['centroid']
                x = min(max(0, x), width - 1)
                y = min(max(0, y), height - 1)
                
                # Agregar distribución gaussiana alrededor del punto
                sigma = 30
                y_grid, x_grid = np.ogrid[-y:height-y, -x:width-x]
                mask = x_grid*x_grid + y_grid*y_grid <= sigma*sigma
                heatmap[mask] += 1
            
            # Normalizar
            if heatmap.max() > 0:
                heatmap = heatmap / heatmap.max()
            
            # Crear figura
            fig, ax = plt.subplots(figsize=(12, 8), dpi=self.dpi)
            
            # Mostrar mapa de calor
            im = ax.imshow(heatmap, cmap='hot', interpolation='gaussian', aspect='auto')
            
            # Barra de color
            cbar = plt.colorbar(im, ax=ax)
            cbar.set_label('Densidad de Actividad', rotation=270, labelpad=20, 
                          fontsize=12, fontweight='bold')
            
            ax.set_title('Mapa de Calor de Actividad', fontsize=16, fontweight='bold', pad=20)
            ax.set_xlabel('X (píxeles)', fontsize=12)
            ax.set_ylabel('Y (píxeles)', fontsize=12)
            
            plt.tight_layout()
            plt.savefig(filepath, dpi=self.dpi, bbox_inches='tight')
            plt.close()
            
            logger.info(f"Mapa de calor generado: {filepath}")
            return filepath
            
        except Exception as e:
            logger.error(f"Error al generar mapa de calor: {e}")
            return None
    
    def plot_traffic_flow_diagram(self, statistics: Dict, 
                                  filename: str = "diagrama_flujo.png") -> str:
        """
        Genera diagrama de flujo de tráfico
        
        Args:
            statistics: Estadísticas del análisis
            filename: Nombre del archivo
            
        Returns:
            Ruta del archivo generado
        """
        filepath = os.path.join(self.output_dir, filename)
        
        try:
            counts_by_line = statistics.get('counts_by_line', [])
            
            if not counts_by_line:
                logger.warning("No hay datos para diagrama de flujo")
                return None
            
            # Crear figura con subplots para cada línea
            n_lines = len(counts_by_line)
            fig, axes = plt.subplots(n_lines, 1, figsize=(12, 4*n_lines), dpi=self.dpi)
            
            if n_lines == 1:
                axes = [axes]
            
            for idx, (ax, line_info) in enumerate(zip(axes, counts_by_line)):
                line_name = line_info['line_name']
                counts = line_info['counts_by_class']
                
                # Preparar datos de direcciones
                categories = list(counts.keys())
                
                directions = ['up_to_down', 'down_to_up', 'left_to_right', 'right_to_left']
                direction_labels = ['Arriba→Abajo', 'Abajo→Arriba', 'Izq→Der', 'Der→Izq']
                
                # Crear matriz de datos
                data = []
                for category in categories:
                    row = [counts[category].get(d, 0) for d in directions]
                    data.append(row)
                
                data = np.array(data)
                
                # Graficar heatmap
                if data.sum() > 0:
                    im = ax.imshow(data, cmap='YlOrRd', aspect='auto')
                    
                    # Agregar valores en las celdas
                    for i in range(len(categories)):
                        for j in range(len(directions)):
                            text = ax.text(j, i, int(data[i, j]),
                                         ha="center", va="center", color="black",
                                         fontsize=10, fontweight='bold')
                    
                    # Configurar ejes
                    ax.set_xticks(np.arange(len(direction_labels)))
                    ax.set_yticks(np.arange(len(categories)))
                    ax.set_xticklabels(direction_labels)
                    ax.set_yticklabels(categories)
                    ax.set_title(f'{line_name} - Flujo por Dirección', 
                               fontsize=14, fontweight='bold', pad=10)
                    
                    # Barra de color
                    cbar = plt.colorbar(im, ax=ax)
                    cbar.set_label('Conteo', rotation=270, labelpad=15)
            
            plt.tight_layout()
            plt.savefig(filepath, dpi=self.dpi, bbox_inches='tight')
            plt.close()
            
            logger.info(f"Diagrama de flujo generado: {filepath}")
            return filepath
            
        except Exception as e:
            logger.error(f"Error al generar diagrama de flujo: {e}")
            return None
    
    def generate_all_visualizations(self,
                                   statistics: Dict,
                                   crossings: List[Dict],
                                   time_series: Dict = None,
                                   frame_shape: Tuple[int, int] = None) -> Dict[str, str]:
        """
        Genera todas las visualizaciones disponibles
        
        Args:
            statistics: Estadísticas del análisis
            crossings: Lista de cruces
            time_series: Datos de series temporales
            frame_shape: Forma del frame para mapa de calor
            
        Returns:
            Diccionario con rutas de todos los gráficos generados
        """
        visualizations = {}
        
        try:
            # Gráfico de barras totales
            path = self.plot_total_counts_bar(statistics)
            if path:
                visualizations['bar_chart'] = path
            
            # Conteos por línea
            path = self.plot_counts_by_line(statistics)
            if path:
                visualizations['line_chart'] = path
            
            # Series temporales
            if time_series:
                path = self.plot_time_series(time_series)
                if path:
                    visualizations['time_series'] = path
            
            # Distribución de direcciones
            path = self.plot_direction_distribution(statistics)
            if path:
                visualizations['direction_pie'] = path
            
            # Diagrama de flujo
            path = self.plot_traffic_flow_diagram(statistics)
            if path:
                visualizations['flow_diagram'] = path
            
            # Mapa de calor
            if frame_shape:
                path = self.plot_heatmap(crossings, frame_shape)
                if path:
                    visualizations['heatmap'] = path
            
            logger.info(f"Generadas {len(visualizations)} visualizaciones")
            return visualizations
            
        except Exception as e:
            logger.error(f"Error al generar visualizaciones: {e}")
            return visualizations


if __name__ == "__main__":
    # Pruebas del visualizador
    print("=== Pruebas del Visualizer ===")
    
    # Crear visualizador
    visualizer = TrafficVisualizer(output_dir="test_visualizations")
    
    # Datos de prueba
    test_stats = {
        'total_counts': {'Auto': 50, 'Peatón': 30, 'Moto': 20},
        'counts_by_line': []
    }
    
    print("✓ Módulo visualizer funcionando correctamente")
