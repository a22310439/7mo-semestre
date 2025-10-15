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
        self.callback = callback
        self.analysis_time = 0
        self.pages_data = []  # Almacenar datos de páginas para búsqueda
        
    def clean_text(self, text: str) -> List[str]:
        text = text.lower()
        words = re.findall(r'\b[a-záéíóúñü]+\b', text)
        return words
    
    def extract_paragraphs(self, text: str) -> List[str]:
        """Divide el texto en párrafos"""
        paragraphs = [p.strip() for p in text.split('\n') if p.strip()]
        return paragraphs
    
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
        start_time = time.time()
        
        if self.callback:
            self.callback(f"Abriendo PDF: {self.pdf_path}")
            self.callback(f"Usando {self.num_workers} workers\n")
        
        try:
            with open(self.pdf_path, 'rb') as file:
                pdf_reader = PyPDF2.PdfReader(file)
                total_pages = len(pdf_reader.pages)
                if self.callback:
                    self.callback(f"Total de páginas: {total_pages}")
                
                # Extraer texto de todas las páginas y guardar para búsqueda
                if self.callback:
                    self.callback("Extrayendo texto...")
                pages_text = []
                self.pages_data = []
                
                for page_num in range(total_pages):
                    page = pdf_reader.pages[page_num]
                    page_text = page.extract_text()
                    pages_text.append((page_num, page_text))
                    
                    # Guardar párrafos de cada página
                    paragraphs = self.extract_paragraphs(page_text)
                    self.pages_data.append({
                        'page_num': page_num + 1,
                        'paragraphs': paragraphs
                    })
                
                # Distribuir páginas entre workers
                batches = self.distribute_pages(total_pages, pages_text)
                if self.callback:
                    self.callback(f"Páginas distribuidas en {len(batches)} lotes\n")
                
                # Procesar con ThreadPoolExecutor
                with ThreadPoolExecutor(max_workers=self.num_workers) as executor:
                    futures = {
                        executor.submit(self.process_pages_batch, batch): i 
                        for i, batch in enumerate(batches)
                    }
                    
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
                
                self.analysis_time = time.time() - start_time
                
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
    
    def search_phrase(self, words: List[str]) -> List[Dict]:
        """
        Busca frases compuestas por las palabras dadas, donde cada palabra
        está separada de las demás por máximo 2 palabras.
        """
        results = []
        words = [w.lower().strip() for w in words if w.strip()]
        
        if not words:
            return results
        
        for page_data in self.pages_data:
            page_num = page_data['page_num']
            
            for para_num, paragraph in enumerate(page_data['paragraphs'], 1):
                # Limpiar y obtener palabras del párrafo
                para_words = self.clean_text(paragraph)
                
                # Buscar la frase en el párrafo
                if self.is_phrase_valid(para_words, words):
                    results.append({
                        'page': page_num,
                        'paragraph': para_num,
                        'context': paragraph[:200] + '...' if len(paragraph) > 200 else paragraph
                    })
        
        return results
    
    def is_phrase_valid(self, text_words: List[str], search_words: List[str]) -> bool:
        """
        Verifica si las palabras de búsqueda aparecen en el texto con máximo 2 palabras de separación.
        """
        if not search_words or not text_words:
            return False
        
        # Para cada posible inicio
        for i in range(len(text_words)):
            if self.check_phrase_from_position(text_words, search_words, i):
                return True
        
        return False
    
    def check_phrase_from_position(self, text_words: List[str], search_words: List[str], start: int) -> bool:
        """
        Verifica si la frase comienza en la posición start con las restricciones de distancia.
        """
        if start >= len(text_words):
            return False
        
        # Si solo hay una palabra, buscar coincidencia directa
        if len(search_words) == 1:
            return search_words[0] in text_words[start:]
        
        # Buscar la primera palabra
        if text_words[start] != search_words[0]:
            return False
        
        current_pos = start
        
        # Para cada palabra subsecuente
        for search_word in search_words[1:]:
            # Buscar la siguiente palabra dentro de las próximas 3 posiciones (0, 1, 2 palabras de separación)
            found = False
            for offset in range(1, 4):  # 1, 2, 3 posiciones adelante
                next_pos = current_pos + offset
                if next_pos < len(text_words) and text_words[next_pos] == search_word:
                    current_pos = next_pos
                    found = True
                    break
            
            if not found:
                return False
        
        return True
    
    def get_top_words(self, n: int = None) -> List[tuple]:
        if n:
            return self.word_counts.most_common(n)
        else:
            return self.word_counts.most_common()

class ScrollableHeatmap(ctk.CTkFrame):
    def __init__(self, master, **kwargs):
        super().__init__(master, **kwargs)
        
        self.canvas = Canvas(self, bg='#212121', highlightthickness=0, bd=0)
        self.scrollbar = ctk.CTkScrollbar(self, orientation="vertical", command=self.canvas.yview)
        self.scrollable_frame = Frame(self.canvas, bg='#212121', bd=0)
        
        self.scrollable_frame.bind(
            "<Configure>",
            lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all"))
        )
        
        self.canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw")
        self.canvas.configure(yscrollcommand=self.scrollbar.set)
        
        self.canvas.pack(side="left", fill="both", expand=True, padx=0, pady=0)
        self.scrollbar.pack(side="right", fill="y", padx=0, pady=0)
        
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
        self.geometry("1400x900")
        
        self.after(10, lambda: self.state('zoomed'))
        
        self.analyzer = None
        self.pdf_path = None
        
        self.setup_ui()
        
    def setup_ui(self):
        # Frame principal con dos columnas
        self.main_container = ctk.CTkFrame(self)
        self.main_container.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Frame superior (controles)
        self.control_frame = ctk.CTkFrame(self.main_container)
        self.control_frame.pack(fill="x", padx=10, pady=10)
        
        self.select_button = ctk.CTkButton(
            self.control_frame, 
            text="Seleccionar PDF", 
            command=self.select_pdf,
            width=150,
            height=40
        )
        self.select_button.pack(side="left", padx=10)
        
        self.file_label = ctk.CTkLabel(
            self.control_frame, 
            text="No se ha seleccionado ningún archivo",
            wraplength=300
        )
        self.file_label.pack(side="left", padx=10, expand=True, fill="x")
        
        self.analyze_button = ctk.CTkButton(
            self.control_frame, 
            text="Analizar PDF", 
            command=self.analyze_pdf,
            width=150,
            height=40,
            state="disabled"
        )
        self.analyze_button.pack(side="left", padx=10)
        
        self.save_button = ctk.CTkButton(
            self.control_frame, 
            text="Guardar Resultados", 
            command=self.save_results,
            width=150,
            height=40,
            state="disabled"
        )
        self.save_button.pack(side="left", padx=10)
        
        # Frame contenedor principal dividido en dos columnas
        self.content_container = ctk.CTkFrame(self.main_container)
        self.content_container.pack(fill="both", expand=True, padx=10, pady=10)
        
        # COLUMNA IZQUIERDA: Log y Estadísticas
        self.left_column = ctk.CTkFrame(self.content_container, width=400)
        self.left_column.pack(side="left", fill="both", expand=False, padx=(0, 5))
        self.left_column.pack_propagate(False)
        
        # Log
        self.log_label = ctk.CTkLabel(self.left_column, text="Registro de Análisis", font=("Arial", 16, "bold"))
        self.log_label.pack(pady=10)
        
        self.log_text = ctk.CTkTextbox(self.left_column, height=300)
        self.log_text.pack(fill="both", expand=True, padx=10, pady=(0, 10))
        
        # Estadísticas
        self.stats_frame = ctk.CTkFrame(self.left_column)
        self.stats_frame.pack(fill="x", padx=10, pady=10)
        
        self.stats_label = ctk.CTkLabel(self.stats_frame, text="Estadísticas", font=("Arial", 14, "bold"))
        self.stats_label.pack(pady=5)
        
        self.unique_words_label = ctk.CTkLabel(self.stats_frame, text="Palabras únicas: -")
        self.unique_words_label.pack()
        
        self.total_words_label = ctk.CTkLabel(self.stats_frame, text="Total de palabras: -")
        self.total_words_label.pack()
        
        self.time_label = ctk.CTkLabel(self.stats_frame, text="Tiempo de análisis: -")
        self.time_label.pack()
        
        # BUSCADOR DE FRASES
        self.search_frame = ctk.CTkFrame(self.left_column)
        self.search_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        self.search_label = ctk.CTkLabel(self.search_frame, text="Buscador de Frases", font=("Arial", 14, "bold"))
        self.search_label.pack(pady=10)
        
        self.search_info = ctk.CTkLabel(
            self.search_frame, 
            text="Ingresa hasta 3 palabras separadas por comas.\nEj: palabra1, palabra2, palabra3",
            font=("Arial", 10),
            text_color="gray"
        )
        self.search_info.pack(pady=5)
        
        # Frame para entrada y botón
        self.search_input_frame = ctk.CTkFrame(self.search_frame)
        self.search_input_frame.pack(fill="x", padx=10, pady=5)
        
        self.phrase_entry = ctk.CTkEntry(
            self.search_input_frame,
            placeholder_text="palabra1, palabra2, palabra3"
        )
        self.phrase_entry.pack(side="left", fill="x", expand=True, padx=(0, 5))
        
        self.search_button = ctk.CTkButton(
            self.search_input_frame,
            text="Buscar",
            command=self.search_phrase,
            width=100,
            state="disabled"
        )
        self.search_button.pack(side="right")
        
        # Resultados de búsqueda
        self.search_results_label = ctk.CTkLabel(self.search_frame, text="Resultados:", font=("Arial", 12, "bold"))
        self.search_results_label.pack(pady=(10, 5))
        
        self.search_results = ctk.CTkTextbox(self.search_frame, height=200)
        self.search_results.pack(fill="both", expand=True, padx=10, pady=(0, 10))
        
        # COLUMNA DERECHA: Mapa de Calor
        self.right_column = ctk.CTkFrame(self.content_container)
        self.right_column.pack(side="right", fill="both", expand=True)
        
        self.heatmap_label = ctk.CTkLabel(self.right_column, text="Mapa de Calor", font=("Arial", 16, "bold"))
        self.heatmap_label.pack(pady=10)
        
        self.info_label = ctk.CTkLabel(self.right_column, text="", font=("Arial", 12))
        self.info_label.pack()
        
        self.canvas_frame = ScrollableHeatmap(self.right_column)
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
        self.log_text.insert("end", f"{message}\n")
        self.log_text.see("end")
        self.update()
    
    def analyze_pdf(self):
        if not self.pdf_path:
            messagebox.showerror("Error", "Por favor selecciona un archivo PDF primero")
            return
        
        self.analyze_button.configure(state="disabled")
        self.select_button.configure(state="disabled")
        self.save_button.configure(state="disabled")
        self.search_button.configure(state="disabled")
        
        self.log_text.delete("0.0", "end")
        self.search_results.delete("0.0", "end")
        
        thread = threading.Thread(target=self.run_analysis)
        thread.start()
    
    def run_analysis(self):
        try:
            self.analyzer = PDFWordAnalyzer(self.pdf_path, callback=self.update_log)
            self.analyzer.analyze()
            
            self.after(0, self.update_stats)
            self.after(0, self.create_heatmap)
            self.after(0, lambda: self.search_button.configure(state="normal"))
            
        except Exception as e:
            self.after(0, lambda: messagebox.showerror("Error", f"Error al analizar el PDF: {str(e)}"))
        finally:
            self.after(0, lambda: self.analyze_button.configure(state="normal"))
            self.after(0, lambda: self.select_button.configure(state="normal"))
            self.after(0, lambda: self.save_button.configure(state="normal"))
    
    def search_phrase(self):
        if not self.analyzer:
            messagebox.showerror("Error", "Primero debes analizar un PDF")
            return
        
        phrase_text = self.phrase_entry.get().strip()
        if not phrase_text:
            messagebox.showwarning("Advertencia", "Ingresa al menos una palabra")
            return
        
        # Separar palabras por comas
        words = [w.strip() for w in phrase_text.split(',') if w.strip()]
        
        if len(words) > 3:
            messagebox.showwarning("Advertencia", "Ingresa máximo 3 palabras")
            return
        
        # Deshabilitar botón durante búsqueda
        self.search_button.configure(state="disabled")
        self.search_results.delete("0.0", "end")
        self.search_results.insert("0.0", "Buscando...\n")
        
        # Ejecutar búsqueda en hilo separado
        thread = threading.Thread(target=self.run_search, args=(words,))
        thread.start()
    
    def run_search(self, words):
        try:
            results = self.analyzer.search_phrase(words)
            self.after(0, lambda: self.display_search_results(words, results))
        except Exception as e:
            self.after(0, lambda: messagebox.showerror("Error", f"Error en la búsqueda: {str(e)}"))
        finally:
            self.after(0, lambda: self.search_button.configure(state="normal"))
    
    def display_search_results(self, words, results):
        self.search_results.delete("0.0", "end")
        
        phrase_display = ", ".join(words)
        self.search_results.insert("0.0", f"Búsqueda: {phrase_display}\n")
        self.search_results.insert("end", f"Resultados encontrados: {len(results)}\n")
        self.search_results.insert("end", "=" * 50 + "\n\n")
        
        if not results:
            self.search_results.insert("end", "No se encontraron coincidencias.\n")
        else:
            for i, result in enumerate(results, 1):
                self.search_results.insert("end", f"[{i}] Página {result['page']}, Párrafo {result['paragraph']}\n")
                self.search_results.insert("end", f"Contexto: {result['context']}\n\n")
    
    def update_stats(self):
        if self.analyzer and self.analyzer.word_counts:
            unique_words = len(self.analyzer.word_counts)
            total_words = sum(self.analyzer.word_counts.values())
            
            self.unique_words_label.configure(text=f"Palabras únicas: {unique_words:,}")
            self.total_words_label.configure(text=f"Total de palabras: {total_words:,}")
            self.time_label.configure(text=f"Tiempo de análisis: {self.analyzer.analysis_time:.2f} segundos")
    
    def create_heatmap(self):
        if not self.analyzer or not self.analyzer.word_counts:
            return
        
        for widget in self.canvas_frame.get_frame().winfo_children():
            widget.destroy()
        
        all_words = self.analyzer.get_top_words(n=None)
        
        if not all_words:
            self.no_data_label = ctk.CTkLabel(
                self.canvas_frame.get_frame(), 
                text="No hay palabras para mostrar después del filtrado",
                font=("Arial", 14)
            )
            self.no_data_label.pack(expand=True, pady=100)
            self.info_label.configure(text="")
            return
        
        self.info_label.configure(text=f"Mostrando {len(all_words)} palabras")
        
        words, frequencies = zip(*all_words)
        total_words = len(words)
        
        row_height = 0.25
        fig_height = max(8, total_words * row_height)
        
        fig = plt.figure(figsize=(10, fig_height), facecolor='#212121')
        ax = fig.add_subplot(111)
        ax.set_facecolor('#212121')
        
        freq_array = np.array(frequencies)
        freq_normalized = (freq_array - freq_array.min()) / (freq_array.max() - freq_array.min())
        
        cmap = plt.cm.get_cmap('YlOrRd')
        
        color_data = np.zeros((total_words, 1))
        for i in range(total_words):
            color_data[i, 0] = freq_normalized[i]
        
        ax.set_xlim(0, 5)
        ax.set_ylim(-1, total_words + 1)
        ax.axis('off')
        
        colorbar_x = 0.3
        colorbar_width = 0.4
        word_x = 1.2
        freq_x = 4.5
        
        im = ax.imshow(color_data, 
                    extent=[colorbar_x, colorbar_x + colorbar_width, -0.5, total_words - 0.5],
                    aspect='auto', 
                    cmap=cmap,
                    interpolation='bilinear')
        
        rect = plt.Rectangle((colorbar_x, -0.5), colorbar_width, total_words, 
                            facecolor='none', edgecolor='white', linewidth=1)
        ax.add_patch(rect)
        
        for i in range(total_words):
            y_position = total_words - i - 1
            word = words[i]
            freq = frequencies[i]
            
            ax.text(word_x, y_position, word, va='center', ha='left', 
                fontsize=10, fontweight='bold', color='white')
            
            ax.text(freq_x, y_position, str(freq), va='center', ha='right', 
                fontsize=10, color='white',
                bbox=dict(boxstyle='round,pad=0.3', facecolor='#424242', 
                        alpha=0.8, edgecolor='none'))
        
        header_y = total_words + 0.2
        ax.text(colorbar_x + colorbar_width/2, header_y, 'Color', 
            va='bottom', ha='center', fontsize=12, fontweight='bold', color='white')
        ax.text(word_x + 0.8, header_y, 'Palabra', 
            va='bottom', ha='center', fontsize=12, fontweight='bold', color='white')
        ax.text(freq_x - 0.2, header_y, 'Frecuencia', 
            va='bottom', ha='center', fontsize=12, fontweight='bold', color='white')
        
        ax.plot([0, 5], [total_words - 0.5, total_words - 0.5], 'w-', linewidth=2)
        
        plt.subplots_adjust(left=0.05, right=0.95, top=0.9998, bottom=0.01)
        
        canvas = FigureCanvasTkAgg(fig, master=self.canvas_frame.get_frame())
        canvas.draw()
        
        canvas_widget = canvas.get_tk_widget()
        canvas_widget.pack(fill="both", expand=True, pady=0)
        
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
                with open(filename, 'w', encoding='utf-8') as f:
                    f.write("ANÁLISIS DE FRECUENCIA DE PALABRAS\n")
                    f.write("=" * 50 + "\n\n")
                    f.write(f"Archivo analizado: {os.path.basename(self.pdf_path)}\n")
                    f.write(f"Workers utilizados: {self.analyzer.num_workers}\n")
                    f.write(f"Tiempo de análisis: {self.analyzer.analysis_time:.2f} segundos\n")
                    f.write(f"Total de palabras únicas: {len(self.analyzer.word_counts)}\n")
                    f.write(f"Total de palabras: {sum(self.analyzer.word_counts.values())}\n\n")
                    
                    f.write("TODAS LAS PALABRAS:\n")
                    f.write("-" * 50 + "\n")
                    
                    all_words = self.analyzer.get_top_words(n=None)
                    for word, count in all_words:
                        f.write(f"{word:30} {count:>10}\n")
                
                messagebox.showinfo("Éxito", f"Resultados guardados en {filename}")
            except Exception as e:
                messagebox.showerror("Error", f"Error al guardar el archivo: {str(e)}")


if __name__ == "__main__":
    app = PDFAnalyzerApp()
    app.mainloop()