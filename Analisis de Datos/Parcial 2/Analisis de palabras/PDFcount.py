import customtkinter as ctk
from tkinter import filedialog, messagebox, Canvas, Frame
import threading
import PyPDF2
from concurrent.futures import ThreadPoolExecutor, as_completed
from collections import Counter
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import numpy as np
import re
import os
import time
from typing import Dict, List, Tuple

# Configurar el tema de customtkinter
ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")

class PDFWordAnalyzer:
    def __init__(self, pdf_path: str, num_workers: int = None, callback=None):
        self.pdf_path = pdf_path
        self.word_counts = Counter()
        self.num_workers = num_workers or os.cpu_count()
        self.callback = callback  # Para actualizar la UI
        self.analysis_time = 0
        
    def clean_text(self, text: str) -> List[str]:
        text = text.lower()
        words = re.findall(r'\b[a-záéíóúñü]+\b', text)
        return words
    
    def process_pages_batch(self, pages_data: List[Tuple[int, str]]) -> Counter:
        batch_counter = Counter()
        
        for page_num, page_text in pages_data:
            words = self.clean_text(page_text)
            batch_counter.update(words)
            if self.callback:
                self.callback(f"✓ Página {page_num + 1} procesada: {len(words)} palabras")
        
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
        start_time = time.time()  # Iniciar contador de tiempo
        
        if self.callback:
            self.callback(f"Abriendo PDF: {self.pdf_path}")
            self.callback(f"Usando {self.num_workers} workers\n")
        
        try:
            with open(self.pdf_path, 'rb') as file:
                pdf_reader = PyPDF2.PdfReader(file)
                total_pages = len(pdf_reader.pages)
                if self.callback:
                    self.callback(f"Total de páginas: {total_pages}")
                
                # Extraer texto de todas las páginas primero
                if self.callback:
                    self.callback("Extrayendo texto...")
                pages_text = []
                for page_num in range(total_pages):
                    page = pdf_reader.pages[page_num]
                    page_text = page.extract_text()
                    pages_text.append((page_num, page_text))
                
                # Distribuir páginas entre workers
                batches = self.distribute_pages(total_pages, pages_text)
                if self.callback:
                    self.callback(f"Páginas distribuidas en {len(batches)} lotes\n")
                
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
                            if self.callback:
                                self.callback(f"→ Lote {batch_num + 1} completado\n")
                        except Exception as e:
                            if self.callback:
                                self.callback(f"Error en lote {batch_num}: {str(e)}")
                
                self.analysis_time = time.time() - start_time  # Calcular tiempo total
                
                if self.callback:
                    self.callback(f"Análisis completado!")
                    self.callback(f"Tiempo de análisis: {self.analysis_time:.2f} segundos")
                    self.callback(f"Total de palabras únicas: {len(self.word_counts)}")
                    self.callback(f"Total de palabras: {sum(self.word_counts.values())}")
                
        except FileNotFoundError:
            if self.callback:
                self.callback(f"Error: No se encontró el archivo {self.pdf_path}")
        except Exception as e:
            if self.callback:
                self.callback(f"Error al procesar el PDF: {str(e)}")
    
    def get_top_words(self, n: int = None, exclude_common: bool = False) -> List[tuple]:
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
            counter = Counter(filtered_counts)
        else:
            counter = self.word_counts
        
        if n:
            return counter.most_common(n)
        else:
            return counter.most_common()  # Retornar todas las palabras

class ScrollableHeatmap(ctk.CTkFrame):
    def __init__(self, master, **kwargs):
        super().__init__(master, **kwargs)
        
        # Canvas y scrollbar
        self.canvas = Canvas(self, bg='#212121', highlightthickness=0, bd=0)  # Sin borde
        self.scrollbar = ctk.CTkScrollbar(self, orientation="vertical", command=self.canvas.yview)
        self.scrollable_frame = Frame(self.canvas, bg='#212121', bd=0)  # Sin borde
        
        self.scrollable_frame.bind(
            "<Configure>",
            lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all"))
        )
        
        self.canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw")
        self.canvas.configure(yscrollcommand=self.scrollbar.set)
        
        self.canvas.pack(side="left", fill="both", expand=True, padx=0, pady=0)
        self.scrollbar.pack(side="right", fill="y", padx=0, pady=0)
        
        # Bind mouse wheel
        self.canvas.bind_all("<MouseWheel>", self._on_mousewheel)
        self.canvas.bind_all("<Button-4>", self._on_mousewheel)
        self.canvas.bind_all("<Button-5>", self._on_mousewheel)

    def _on_mousewheel(self, event):
        if event.delta:
            self.canvas.yview_scroll(int(-1*(event.delta/120)), "units")
        elif event.num == 4:
            self.canvas.yview_scroll(-1, "units")
        elif event.num == 5:
            self.canvas.yview_scroll(1, "units")
    
    def get_frame(self):
        return self.scrollable_frame

class PDFAnalyzerApp(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("Analizador de Palabras en PDF")
        self.geometry("1200x800")
        
        # Maximizar la ventana después de inicializar
        self.after(10, lambda: self.state('zoomed'))
        
        # Inicializar variables
        self.analyzer = None
        self.pdf_path = None
        self.exclude_common_var = ctk.BooleanVar(value=False)
        
        self.setup_ui()
        
    def setup_ui(self):
        # Frame principal
        self.main_container = ctk.CTkFrame(self)
        self.main_container.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Frame superior (controles)
        self.control_frame = ctk.CTkFrame(self.main_container)
        self.control_frame.pack(fill="x", padx=10, pady=10)
        
        # Botón para seleccionar PDF
        self.select_button = ctk.CTkButton(
            self.control_frame, 
            text="Seleccionar PDF", 
            command=self.select_pdf,
            width=150,
            height=40
        )
        self.select_button.pack(side="left", padx=10)
        
        # Label para mostrar el archivo seleccionado
        self.file_label = ctk.CTkLabel(
            self.control_frame, 
            text="No se ha seleccionado ningún archivo",
            wraplength=300
        )
        self.file_label.pack(side="left", padx=10, expand=True, fill="x")
        
        # Botón para analizar
        self.analyze_button = ctk.CTkButton(
            self.control_frame, 
            text="Analizar PDF", 
            command=self.analyze_pdf,
            width=150,
            height=40,
            state="disabled"
        )
        self.analyze_button.pack(side="left", padx=10)
        
        
        # Botón para guardar resultados
        self.save_button = ctk.CTkButton(
            self.control_frame, 
            text="Guardar Resultados", 
            command=self.save_results,
            width=150,
            height=40,
            state="disabled"
        )
        self.save_button.pack(side="left", padx=10)
        
        # Frame contenedor para el contenido principal (dividido en dos)
        self.content_frame = ctk.CTkFrame(self.main_container)
        self.content_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Frame izquierdo para el log
        self.log_frame = ctk.CTkFrame(self.content_frame, width=400)
        self.log_frame.pack(side="left", fill="y", padx=(0, 5))
        self.log_frame.pack_propagate(False)
        
        self.log_label = ctk.CTkLabel(self.log_frame, text="Registro de Análisis", font=("Arial", 16, "bold"))
        self.log_label.pack(pady=10)
        
        # Textbox para mostrar el progreso
        self.log_text = ctk.CTkTextbox(self.log_frame, height=400)
        self.log_text.pack(fill="both", expand=True, padx=10, pady=(0, 10))
        
        # Frame para estadísticas
        self.stats_frame = ctk.CTkFrame(self.log_frame)
        self.stats_frame.pack(fill="x", padx=10, pady=10)
        
        self.stats_label = ctk.CTkLabel(self.stats_frame, text="Estadísticas", font=("Arial", 14, "bold"))
        self.stats_label.pack(pady=5)
        
        self.unique_words_label = ctk.CTkLabel(self.stats_frame, text="Palabras únicas: -")
        self.unique_words_label.pack()
        
        self.total_words_label = ctk.CTkLabel(self.stats_frame, text="Total de palabras: -")
        self.total_words_label.pack()
        
        self.time_label = ctk.CTkLabel(self.stats_frame, text="Tiempo de análisis: -")
        self.time_label.pack()
        
        # Frame derecho para el mapa de calor
        self.heatmap_frame = ctk.CTkFrame(self.content_frame)
        self.heatmap_frame.pack(side="right", fill="both", expand=True)
        
        self.heatmap_label = ctk.CTkLabel(self.heatmap_frame, text="Mapa de Calor", font=("Arial", 16, "bold"))
        self.heatmap_label.pack(pady=10)
        
        # Info label para mostrar número de palabras mostradas
        self.info_label = ctk.CTkLabel(self.heatmap_frame, text="", font=("Arial", 12))
        self.info_label.pack()
        
        # Frame scrollable para el mapa de calor
        self.canvas_frame = ScrollableHeatmap(self.heatmap_frame)
        self.canvas_frame.pack(fill="both", expand=True, padx=10, pady=(0, 10))
        
        self.no_data_label = ctk.CTkLabel(
            self.canvas_frame.get_frame(), 
            text="Selecciona un PDF y haz clic en 'Analizar' para ver el mapa de calor",
            font=("Arial", 14)
        )
        self.no_data_label.pack(expand=True, pady=100)
    
    def select_pdf(self):
        filename = filedialog.askopenfilename(
            title="Seleccionar archivo PDF",
            filetypes=[("PDF files", "*.pdf"), ("All files", "*.*")]
        )
        
        if filename:
            self.pdf_path = filename
            self.file_label.configure(text=f"Archivo: {os.path.basename(filename)}")
            self.analyze_button.configure(state="normal")
            self.log_text.delete("0.0", "end")
            self.log_text.insert("0.0", f"Archivo seleccionado: {filename}\n")
    
    def update_log(self, message):
        """Actualiza el log en el hilo principal de la UI"""
        self.log_text.insert("end", f"{message}\n")
        self.log_text.see("end")
        self.update()
    
    def analyze_pdf(self):
        if not self.pdf_path:
            messagebox.showerror("Error", "Por favor selecciona un archivo PDF primero")
            return
        
        # Deshabilitar botones durante el análisis
        self.analyze_button.configure(state="disabled")
        self.select_button.configure(state="disabled")
        self.save_button.configure(state="disabled")
        
        # Limpiar log
        self.log_text.delete("0.0", "end")
        
        # Ejecutar análisis en un hilo separado
        thread = threading.Thread(target=self.run_analysis)
        thread.start()
    
    def run_analysis(self):
        try:
            self.analyzer = PDFWordAnalyzer(self.pdf_path, callback=self.update_log)
            self.analyzer.analyze()
            
            # Actualizar estadísticas en el hilo principal
            self.after(0, self.update_stats)
            self.after(0, self.create_heatmap)
            
        except Exception as e:
            self.after(0, lambda: messagebox.showerror("Error", f"Error al analizar el PDF: {str(e)}"))
        finally:
            # Rehabilitar botones
            self.after(0, lambda: self.analyze_button.configure(state="normal"))
            self.after(0, lambda: self.select_button.configure(state="normal"))
            self.after(0, lambda: self.save_button.configure(state="normal"))
    
    def update_stats(self):
        if self.analyzer and self.analyzer.word_counts:
            unique_words = len(self.analyzer.word_counts)
            total_words = sum(self.analyzer.word_counts.values())
            
            self.unique_words_label.configure(text=f"Palabras únicas: {unique_words:,}")
            self.total_words_label.configure(text=f"Total de palabras: {total_words:,}")
            self.time_label.configure(text=f"Tiempo de análisis: {self.analyzer.analysis_time:.2f} segundos")
    
    def update_heatmap(self):
        if self.analyzer and self.analyzer.word_counts:
            self.create_heatmap()
    
    def create_heatmap(self):
        if not self.analyzer or not self.analyzer.word_counts:
            return
        
        # Limpiar el canvas anterior
        for widget in self.canvas_frame.get_frame().winfo_children():
            widget.destroy()
        
        # Obtener configuración
        exclude_common = self.exclude_common_var.get()
        
        # Obtener todas las palabras
        all_words = self.analyzer.get_top_words(n=None, exclude_common=exclude_common)
        
        if not all_words:
            self.no_data_label = ctk.CTkLabel(
                self.canvas_frame.get_frame(), 
                text="No hay palabras para mostrar después del filtrado",
                font=("Arial", 14)
            )
            self.no_data_label.pack(expand=True, pady=100)
            self.info_label.configure(text="")
            return
        
        # Actualizar info label
        filter_text = " (sin palabras comunes)" if exclude_common else ""
        self.info_label.configure(text=f"Mostrando {len(all_words)} palabras{filter_text}")
        
        # Crear figura de matplotlib
        # Calcular altura basada en número de palabras
        words, frequencies = zip(*all_words)
        total_words = len(words)
        
        # Altura de la figura basada en el número de palabras
        row_height = 0.25  # Altura por palabra en pulgadas
        fig_height = max(8, total_words * row_height)
        
        # Crear figura
        fig = plt.figure(figsize=(10, fig_height), facecolor='#212121')
        
        # Crear un solo eje para todo
        ax = fig.add_subplot(111)
        ax.set_facecolor('#212121')
        
        # Normalizar frecuencias para el colormap
        freq_array = np.array(frequencies)
        freq_normalized = (freq_array - freq_array.min()) / (freq_array.max() - freq_array.min())
        
        # Obtener el colormap
        cmap = plt.cm.get_cmap('YlOrRd')
        
        # Crear datos para la barra de color continua
        # Necesitamos crear una matriz 2D para imshow
        color_data = np.zeros((total_words, 1))
        for i in range(total_words):
            # Invertir el índice para que las palabras más frecuentes estén arriba
            color_data[i, 0] = freq_normalized[i]
        
        # Configurar límites del eje
        ax.set_xlim(0, 5)
        ax.set_ylim(-1, total_words + 1)
        
        # Ocultar ejes
        ax.axis('off')
        
        # Posiciones X para las columnas
        colorbar_x = 0.3
        colorbar_width = 0.4
        word_x = 1.2
        freq_x = 4.5
        
        # Dibujar la barra de color continua usando imshow
        im = ax.imshow(color_data, 
                    extent=[colorbar_x, colorbar_x + colorbar_width, -0.5, total_words - 0.5],
                    aspect='auto', 
                    cmap=cmap,
                    interpolation='bilinear')  # Suavizar los colores
        
        # Agregar borde a la barra de color
        rect = plt.Rectangle((colorbar_x, -0.5), colorbar_width, total_words, 
                            facecolor='none', edgecolor='white', linewidth=1)
        ax.add_patch(rect)
        
        # Agregar texto para cada palabra
        for i in range(total_words):
            y_position = total_words - i - 1
            word = words[i]
            freq = frequencies[i]
            
            # Palabra
            ax.text(word_x, y_position, word, va='center', ha='left', 
                fontsize=10, fontweight='bold', color='white')
            
            # Frecuencia
            ax.text(freq_x, y_position, str(freq), va='center', ha='right', 
                fontsize=10, color='white',
                bbox=dict(boxstyle='round,pad=0.3', facecolor='#424242', 
                        alpha=0.8, edgecolor='none'))
        
        # Agregar encabezados
        header_y = total_words + 0.2
        ax.text(colorbar_x + colorbar_width/2, header_y, 'Color', 
            va='bottom', ha='center', fontsize=12, fontweight='bold', color='white')
        ax.text(word_x + 0.8, header_y, 'Palabra', 
            va='bottom', ha='center', fontsize=12, fontweight='bold', color='white')
        ax.text(freq_x - 0.2, header_y, 'Frecuencia', 
            va='bottom', ha='center', fontsize=12, fontweight='bold', color='white')
        
        # Línea separadora del encabezado
        ax.plot([0, 5], [total_words - 0.5, total_words - 0.5], 'w-', linewidth=2)
        
        # Título
        title = f''
        if exclude_common:
            title += '\n(sin palabras comunes)'
        ax.text(2.5, total_words + 0.8, title, 
            va='bottom', ha='center', fontsize=14, fontweight='bold', color='white')
        
        # Ajustar márgenes para eliminar espacio en blanco
        plt.subplots_adjust(left=0.05, right=0.95, top=0.9998, bottom=0.01)
        
        # Crear canvas de tkinter para mostrar la figura
        canvas = FigureCanvasTkAgg(fig, master=self.canvas_frame.get_frame())
        canvas.draw()
        
        # Widget del canvas
        canvas_widget = canvas.get_tk_widget()
        canvas_widget.pack(fill="both", expand=True, pady=0)  # Sin padding vertical
        
        # Cerrar la figura para liberar memoria
        plt.close(fig)
    
    def save_results(self):
        if not self.analyzer or not self.analyzer.word_counts:
            messagebox.showerror("Error", "No hay resultados para guardar")
            return
        
        filename = filedialog.asksaveasfilename(
            defaultextension=".txt",
            filetypes=[("Text files", "*.txt"), ("All files", "*.*")]
        )
        
        if filename:
            try:
                exclude_common = self.exclude_common_var.get()
                
                with open(filename, 'w', encoding='utf-8') as f:
                    f.write("ANÁLISIS DE FRECUENCIA DE PALABRAS\n")
                    f.write("=" * 50 + "\n\n")
                    f.write(f"Archivo analizado: {os.path.basename(self.pdf_path)}\n")
                    f.write(f"Workers utilizados: {self.analyzer.num_workers}\n")
                    f.write(f"Tiempo de análisis: {self.analyzer.analysis_time:.2f} segundos\n")
                    f.write(f"Total de palabras únicas: {len(self.analyzer.word_counts)}\n")
                    f.write(f"Total de palabras: {sum(self.analyzer.word_counts.values())}\n\n")
                    
                    if exclude_common:
                        f.write("TODAS LAS PALABRAS (SIN PALABRAS COMUNES):\n")
                    else:
                        f.write("TODAS LAS PALABRAS:\n")
                    f.write("-" * 50 + "\n")
                    
                    all_words = self.analyzer.get_top_words(n=None, exclude_common=exclude_common)
                    for word, count in all_words:
                        f.write(f"{word:30} {count:>10}\n")
                
                messagebox.showinfo("Éxito", f"Resultados guardados en {filename}")
            except Exception as e:
                messagebox.showerror("Error", f"Error al guardar el archivo: {str(e)}")


if __name__ == "__main__":
    app = PDFAnalyzerApp()
    app.mainloop()