import PyPDF2
from concurrent.futures import ThreadPoolExecutor, as_completed
from collections import Counter
import matplotlib.pyplot as plt
import numpy as np
import re
import os
from typing import Dict, List, Tuple

class PDFWordAnalyzer:
    def __init__(self, pdf_path: str, num_workers: int = None):
        self.pdf_path = pdf_path
        self.word_counts = Counter()
        self.num_workers = num_workers or os.cpu_count()
        
    def clean_text(self, text: str) -> List[str]:
        text = text.lower()
        words = re.findall(r'\b[a-záéíóúñü]+\b', text)
        return words
    
    def process_pages_batch(self, pages_data: List[Tuple[int, str]]) -> Counter:
        batch_counter = Counter()
        
        for page_num, page_text in pages_data:
            words = self.clean_text(page_text)
            batch_counter.update(words)
            print(f"✓ Página {page_num + 1} procesada: {len(words)} palabras")
        
        return batch_counter
    
    def distribute_pages(self, total_pages: int, pages_text: List[Tuple[int, str]]) -> List[List[Tuple[int, str]]]:
        pages_per_worker = max(1, total_pages // self.num_workers)
        batches = []
        
        for i in range(0, total_pages, pages_per_worker):
            batch = pages_text[i:i + pages_per_worker]
            if batch:
                batches.append(batch)
        
        return batches
    
    def analyze(self):
        print(f"Abriendo PDF: {self.pdf_path}")
        print(f"Usando {self.num_workers} workers\n")
        
        try:
            with open(self.pdf_path, 'rb') as file:
                pdf_reader = PyPDF2.PdfReader(file)
                total_pages = len(pdf_reader.pages)
                print(f"Total de páginas: {total_pages}")
                
                # Extraer texto de todas las páginas primero
                print("Extrayendo texto...")
                pages_text = []
                for page_num in range(total_pages):
                    page = pdf_reader.pages[page_num]
                    page_text = page.extract_text()
                    pages_text.append((page_num, page_text))
                
                # Distribuir páginas entre workers
                batches = self.distribute_pages(total_pages, pages_text)
                print(f"Páginas distribuidas en {len(batches)} lotes\n")
                
                # Procesar con ThreadPoolExecutor
                with ThreadPoolExecutor(max_workers=self.num_workers) as executor:
                    # Enviar trabajos
                    futures = {
                        executor.submit(self.process_pages_batch, batch): i 
                        for i, batch in enumerate(batches)
                    }
                    
                    # Recolectar resultados a medida que se completan
                    for future in as_completed(futures):
                        batch_num = futures[future]
                        try:
                            batch_counter = future.result()
                            self.word_counts.update(batch_counter)
                            print(f"→ Lote {batch_num + 1} completado\n")
                        except Exception as e:
                            print(f"Error en lote {batch_num}: {str(e)}")
                
                print(f"Análisis completado!")
                print(f"Total de palabras únicas: {len(self.word_counts)}")
                print(f"Total de palabras: {sum(self.word_counts.values())}")
                
        except FileNotFoundError:
            print(f"Error: No se encontró el archivo {self.pdf_path}")
        except Exception as e:
            print(f"Error al procesar el PDF: {str(e)}")
    
    def get_top_words(self, n: int = 20, exclude_common: bool = False) -> List[tuple]:
        if exclude_common:
            # Stop words comunes en español
            stop_words = {
                'el', 'la', 'de', 'que', 'y', 'a', 'en', 'un', 'ser', 'se',
                'no', 'haber', 'por', 'con', 'su', 'para', 'como', 'estar',
                'tener', 'le', 'lo', 'todo', 'pero', 'más', 'hacer', 'o',
                'poder', 'decir', 'este', 'ir', 'otro', 'ese', 'si', 'me',
                'ya', 'ver', 'porque', 'dar', 'cuando', 'él', 'muy', 'sin',
                'vez', 'mucho', 'saber', 'qué', 'sobre', 'mi', 'alguno',
                'mismo', 'yo', 'también', 'hasta', 'año', 'dos', 'querer',
                'entre', 'así', 'primero', 'desde', 'grande', 'eso', 'ni',
                'nos', 'llegar', 'pasar', 'tiempo', 'ella', 'sí', 'día',
                'uno', 'bien', 'poco', 'deber', 'entonces', 'poner', 'cosa',
                'tanto', 'hombre', 'parecer', 'nuestro', 'tan', 'donde',
                'ahora', 'parte', 'después', 'vida', 'quedar', 'siempre',
                'creer', 'hablar', 'llevar', 'dejar', 'nada', 'cada', 'seguir',
                'menos', 'nuevo', 'encontrar', 'algo', 'solo', 'decir', 'salir',
                'volver', 'tomar', 'conocer', 'vivir', 'sentir', 'tratar',
                'mirar', 'contar', 'empezar', 'esperar', 'buscar', 'existir',
                'entrar', 'trabajar', 'escribir', 'perder', 'producir', 'ocurrir'
            }
            filtered_counts = {
                word: count for word, count in self.word_counts.items()
                if word not in stop_words and len(word) > 2
            }
            return Counter(filtered_counts).most_common(n)
        
        return self.word_counts.most_common(n)
    
    def plot_heatmap(self, exclude_common: bool = False, figsize: tuple = None, 
                    colormap: str = 'YlOrRd', max_words: int = None, 
                    interactive: bool = True):
        if not self.word_counts:
            print("No hay datos para graficar. Ejecuta analyze() primero.")
            return
        
        # Obtener todas las palabras ordenadas por frecuencia
        if exclude_common:
            stop_words = {
                'el', 'la', 'de', 'que', 'y', 'a', 'en', 'un', 'ser', 'se',
                'no', 'haber', 'por', 'con', 'su', 'para', 'como', 'estar',
                'tener', 'le', 'lo', 'todo', 'pero', 'más', 'hacer', 'o',
                'poder', 'decir', 'este', 'ir', 'otro', 'ese', 'si', 'me',
                'ya', 'ver', 'porque', 'dar', 'cuando', 'él', 'muy', 'sin',
                'vez', 'mucho', 'saber', 'qué', 'sobre', 'mi', 'alguno',
                'mismo', 'yo', 'también', 'hasta', 'año', 'dos', 'querer',
                'entre', 'así', 'primero', 'desde', 'grande', 'eso', 'ni',
                'nos', 'llegar', 'pasar', 'tiempo', 'ella', 'sí', 'día',
                'uno', 'bien', 'poco', 'deber', 'entonces', 'poner', 'cosa',
                'tanto', 'hombre', 'parecer', 'nuestro', 'tan', 'donde',
                'ahora', 'parte', 'después', 'vida', 'quedar', 'siempre',
                'creer', 'hablar', 'llevar', 'dejar', 'nada', 'cada', 'seguir',
                'menos', 'nuevo', 'encontrar', 'algo', 'solo', 'decir', 'salir',
                'volver', 'tomar', 'conocer', 'vivir', 'sentir', 'tratar',
                'mirar', 'contar', 'empezar', 'esperar', 'buscar', 'existir',
                'entrar', 'trabajar', 'escribir', 'perder', 'producir', 'ocurrir'
            }
            filtered_counts = {
                word: count for word, count in self.word_counts.items()
                if word not in stop_words and len(word) > 2
            }
            sorted_words = Counter(filtered_counts).most_common()
        else:
            sorted_words = self.word_counts.most_common()
        
        if not sorted_words:
            print("No hay palabras para mostrar después del filtrado.")
            return
        
        # Limitar número de palabras si se especifica
        if max_words:
            sorted_words = sorted_words[:max_words]
        
        words, frequencies = zip(*sorted_words)
        total_words = len(words)
        
        print(f"\nGenerando mapa de calor con {total_words} palabras...")
        
        # Normalizar frecuencias para el colormap
        freq_array = np.array(frequencies)
        freq_normalized = (freq_array - freq_array.min()) / (freq_array.max() - freq_array.min())
        
        # Calcular tamaño de figura
        if figsize is None:
            figsize = (14, 10)
        
        if interactive:
            print(f"   Modo interactivo: usa scroll o rueda del mouse")
        
        # Crear figura y ejes
        fig, ax = plt.subplots(figsize=figsize)
        
        # Obtener el colormap
        cmap = plt.cm.get_cmap(colormap)
        
        # Configurar el eje
        ax.set_xlim(0, 3)
        
        # Ocultar ejes
        ax.spines['top'].set_visible(False)
        ax.spines['right'].set_visible(False)
        ax.spines['bottom'].set_visible(False)
        ax.spines['left'].set_visible(False)
        ax.set_xticks([])
        ax.set_yticks([])
        
        # Variables para almacenar objetos dibujados
        drawn_objects = {'rectangles': [], 'texts': []}
        row_height = 1.0
        
        def draw_visible_words(y_min, y_max):
            # Limpiar objetos anteriores
            for rect in drawn_objects['rectangles']:
                rect.remove()
            for text in drawn_objects['texts']:
                text.remove()
            drawn_objects['rectangles'].clear()
            drawn_objects['texts'].clear()
            
            # Dibujar palabras visibles
            for i in range(total_words):
                # La palabra más frecuente (índice 0) está en la posición Y más alta
                y_position = total_words - i - 1
                
                # Verificar si está en el rango visible
                if y_position < y_min or y_position > y_max:
                    continue
                    
                word = words[i]
                freq = frequencies[i]
                
                # Posición Y para el centro del texto
                y_center = y_position + 0.5
                
                # Columna 1: Barra de color
                color = cmap(freq_normalized[i])
                rect = plt.Rectangle((0, y_position), 0.3, row_height, 
                                facecolor=color, edgecolor='white', linewidth=0.5)
                ax.add_patch(rect)
                drawn_objects['rectangles'].append(rect)
                
                # Columna 2: Palabra
                text1 = ax.text(0.4, y_center, word, va='center', ha='left', 
                            fontsize=9, fontweight='bold')
                drawn_objects['texts'].append(text1)
                
                # Columna 3: Frecuencia
                text2 = ax.text(2.8, y_center, str(freq), va='center', ha='right', 
                            fontsize=9, 
                            bbox=dict(boxstyle='round,pad=0.3', facecolor='lightgray', 
                                    alpha=0.5, edgecolor='none'))
                drawn_objects['texts'].append(text2)
        
        # Configurar vista inicial y límites
        if total_words > 30:
            initial_bottom = total_words - 30
            initial_top = total_words
        else:
            initial_bottom = 0
            initial_top = total_words
        
        # Establecer límites del eje Y (con espacio para el encabezado)
        ax.set_ylim(initial_bottom, total_words + 1)
        
        # Agregar encabezados (fijos)
        header_y = total_words + 0.5
        ax.text(0.15, header_y, 'Color', va='center', ha='center', fontsize=12, fontweight='bold')
        ax.text(1.15, header_y, 'Palabra', va='center', ha='center', fontsize=12, fontweight='bold')
        ax.text(2.5, header_y, 'Frecuencia', va='center', ha='center', fontsize=12, fontweight='bold')
        
        # Líneas separadoras de encabezado
        ax.plot([0, 3], [total_words + 0.2, total_words + 0.2], 'k-', linewidth=2)
        ax.plot([0, 3], [total_words, total_words], 'k-', linewidth=1)
        
        # Título
        title = f'Mapa de Calor de Frecuencia de Palabras\n({total_words} palabras'
        if exclude_common:
            title += ', sin palabras comunes'
        title += ')'
        plt.title(title, fontsize=14, fontweight='bold', pad=20)
        
        # Agregar colorbar
        sm = plt.cm.ScalarMappable(cmap=cmap, norm=plt.Normalize(vmin=freq_array.min(), vmax=freq_array.max()))
        sm.set_array([])
        cbar = plt.colorbar(sm, ax=ax, orientation='vertical', pad=0.02, fraction=0.02)
        cbar.set_label('Escala de Frecuencia', rotation=270, labelpad=20, fontsize=11, fontweight='bold')
        
        # Dibujar palabras iniciales
        draw_visible_words(initial_bottom, initial_top)
        
        # Habilitar scroll si está en modo interactivo
        if interactive:
            def on_scroll(event):
                ylim = ax.get_ylim()
                current_bottom = ylim[0]
                current_top = ylim[1]
                
                # Altura de la ventana visible
                view_height = current_top - current_bottom
                
                if event.button == 'up':
                    # Scroll hacia arriba
                    new_bottom = min(total_words + 1 - view_height, current_bottom + 3)
                    new_top = new_bottom + view_height
                elif event.button == 'down':
                    # Scroll hacia abajo
                    new_bottom = max(0, current_bottom - 3)
                    new_top = new_bottom + view_height
                else:
                    return
                
                # Asegurar que no excedamos los límites
                if new_top > total_words + 1:
                    new_top = total_words + 1
                    new_bottom = max(0, new_top - view_height)
                
                ax.set_ylim(new_bottom, new_top)
                
                # Redibujar solo palabras visibles
                draw_visible_words(new_bottom, new_top)
                fig.canvas.draw_idle()
            
            # Conectar evento de scroll
            fig.canvas.mpl_connect('scroll_event', on_scroll)
        
        plt.tight_layout()
        plt.show()
        
        print(f"✓ Mapa de calor generado con {total_words} palabras")
    
    def save_results(self, output_file: str = 'word_frequencies.txt'):
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write("ANÁLISIS DE FRECUENCIA DE PALABRAS\n")
            f.write("=" * 50 + "\n\n")
            f.write(f"Workers utilizados: {self.num_workers}\n")
            f.write(f"Total de palabras únicas: {len(self.word_counts)}\n")
            f.write(f"Total de palabras: {sum(self.word_counts.values())}\n\n")
            f.write("PALABRAS MÁS FRECUENTES:\n")
            f.write("-" * 50 + "\n")
            
            for word, count in self.get_top_words(50):
                f.write(f"{word:30} {count:>10}\n")
        
        print(f"\n✓ Resultados guardados en {output_file}")


# Ejemplo de uso
if __name__ == "__main__":
    # Especifica la ruta de tu archivo PDF
    pdf_path = "pandas.pdf"
    
    # Crear el analizador (usa CPUs disponibles automáticamente)
    analyzer = PDFWordAnalyzer(pdf_path)
    
    # Analizar el PDF con thread pool optimizado
    analyzer.analyze()
    
    # Mostrar las 10 palabras más frecuentes
    print("\nTop 10 palabras más frecuentes:")
    print("-" * 40)
    for word, count in analyzer.get_top_words(10):
        print(f"{word:20} {count:>5} veces")
    
    analyzer.plot_heatmap(exclude_common=False, colormap='YlOrRd', interactive=True)
    
    # Guardar resultados
    analyzer.save_results()