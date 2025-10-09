import PyPDF2
import threading
from collections import Counter
import matplotlib.pyplot as plt
import re
from typing import Dict, List

class PDFWordAnalyzer:
    def __init__(self, pdf_path: str):
        """
        Inicializa el analizador con la ruta del PDF
        
        Args:
            pdf_path: Ruta al archivo PDF
        """
        self.pdf_path = pdf_path
        self.word_counts = Counter()
        self.lock = threading.Lock()
        
    def clean_text(self, text: str) -> List[str]:
        """
        Limpia el texto y extrae palabras
        
        Args:
            text: Texto a limpiar
            
        Returns:
            Lista de palabras limpias en minúsculas
        """
        # Convertir a minúsculas y extraer solo palabras
        text = text.lower()
        words = re.findall(r'\b[a-záéíóúñü]+\b', text)
        return words
    
    def process_page(self, page_num: int, page_text: str):
        """
        Procesa una página y cuenta las palabras
        
        Args:
            page_num: Número de página
            page_text: Texto de la página
        """
        words = self.clean_text(page_text)
        local_counter = Counter(words)
        
        # Usar lock para actualizar el contador compartido de forma segura
        with self.lock:
            self.word_counts.update(local_counter)
            print(f"✓ Página {page_num + 1} procesada: {len(words)} palabras")
    
    def analyze(self):
        """
        Analiza el PDF usando múltiples hilos
        """
        print(f"Abriendo PDF: {self.pdf_path}")
        
        try:
            with open(self.pdf_path, 'rb') as file:
                pdf_reader = PyPDF2.PdfReader(file)
                total_pages = len(pdf_reader.pages)
                print(f"Total de páginas: {total_pages}\n")
                
                threads = []
                
                # Crear un hilo por cada página
                for page_num in range(total_pages):
                    page = pdf_reader.pages[page_num]
                    page_text = page.extract_text()
                    
                    thread = threading.Thread(
                        target=self.process_page,
                        args=(page_num, page_text)
                    )
                    threads.append(thread)
                    thread.start()
                
                # Esperar a que todos los hilos terminen
                for thread in threads:
                    thread.join()
                
                print(f"\n✓ Análisis completado!")
                print(f"Total de palabras únicas: {len(self.word_counts)}")
                print(f"Total de palabras: {sum(self.word_counts.values())}")
                
        except FileNotFoundError:
            print(f"Error: No se encontró el archivo {self.pdf_path}")
        except Exception as e:
            print(f"Error al procesar el PDF: {str(e)}")
    
    def get_top_words(self, n: int = 20) -> List[tuple]:
        """
        Obtiene las N palabras más frecuentes
        
        Args:
            n: Número de palabras a retornar
            
        Returns:
            Lista de tuplas (palabra, frecuencia)
        """
        return self.word_counts.most_common(n)
    
    def plot_histogram(self, top_n: int = 20, figsize: tuple = (12, 6)):
        """
        Genera un histograma con las palabras más frecuentes
        
        Args:
            top_n: Número de palabras a mostrar
            figsize: Tamaño de la figura (ancho, alto)
        """
        if not self.word_counts:
            print("No hay datos para graficar. Ejecuta analyze() primero.")
            return
        
        top_words = self.get_top_words(top_n)
        words, frequencies = zip(*top_words)
        
        plt.figure(figsize=figsize)
        plt.bar(range(len(words)), frequencies, color='steelblue', edgecolor='navy')
        plt.xlabel('Palabras', fontsize=12, fontweight='bold')
        plt.ylabel('Frecuencia', fontsize=12, fontweight='bold')
        plt.title(f'Top {top_n} Palabras Más Frecuentes en el PDF', 
                  fontsize=14, fontweight='bold')
        plt.xticks(range(len(words)), words, rotation=45, ha='right')
        plt.tight_layout()
        plt.grid(axis='y', alpha=0.3)
        
        # Añadir valores encima de las barras
        for i, freq in enumerate(frequencies):
            plt.text(i, freq, str(freq), ha='center', va='bottom', fontsize=9)
        
        plt.show()
    
    def save_results(self, output_file: str = 'word_frequencies.txt'):
        """
        Guarda los resultados en un archivo de texto
        
        Args:
            output_file: Nombre del archivo de salida
        """
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write("ANÁLISIS DE FRECUENCIA DE PALABRAS\n")
            f.write("=" * 50 + "\n\n")
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
    pdf_path = "pandas.pdf"  # Cambia esto por tu archivo
    
    # Crear el analizador
    analyzer = PDFWordAnalyzer(pdf_path)
    
    # Analizar el PDF con múltiples hilos
    analyzer.analyze()
    
    # Mostrar las 10 palabras más frecuentes
    print("\nTop 10 palabras más frecuentes:")
    print("-" * 40)
    for word, count in analyzer.get_top_words(10):
        print(f"{word:20} {count:>5} veces")
    
    # Generar histograma
    analyzer.plot_histogram(top_n=15)
    
    # Guardar resultados en archivo
    analyzer.save_results()