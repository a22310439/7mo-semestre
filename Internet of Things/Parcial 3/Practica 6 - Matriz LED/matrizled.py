from machine import Pin, SPI
import time

class MAX7219:
    def __init__(self, spi, cs):
        self.spi = spi
        self.cs = cs
        self.cs.value(1)
        self.buffer = bytearray(8)
        self.init_display()
    
    def write_command(self, register, data):
        """Envía comando al MAX7219"""
        self.cs.value(0)
        self.spi.write(bytearray([register, data]))
        self.cs.value(1)
    
    def init_display(self):
        """Inicializa la matriz"""
        self.write_command(0x09, 0x00)  # Modo sin decodificación
        self.write_command(0x0A, 0x05)  # Intensidad media (0x00-0x0F)
        self.write_command(0x0B, 0x07)  # Mostrar todas las filas
        self.write_command(0x0C, 0x01)  # Encender display
        self.write_command(0x0F, 0x00)  # Modo normal (no test)
        self.clear()
    
    def clear(self):
        """Limpia la matriz"""
        for i in range(8):
            self.write_command(i + 1, 0x00)
            self.buffer[i] = 0x00
    
    def set_brightness(self, level):
        """Ajusta brillo (0-15)"""
        self.write_command(0x0A, level & 0x0F)
    
    def display_column(self, col, data):
        """Muestra datos en una columna (1-8)"""
        if 1 <= col <= 8:
            self.write_command(col, data)
            self.buffer[col - 1] = data
    
    def display_buffer(self, buffer):
        """Muestra un buffer completo de 8 bytes"""
        for i in range(8):
            self.display_column(i + 1, buffer[i])

# Fuente 5x7 para letras mayúsculas (cada letra tiene 5 columnas)
FONT = {
    'C': [0x3E, 0x41, 0x41, 0x41, 0x22],
    'E': [0x7F, 0x49, 0x49, 0x49, 0x41],
    'T': [0x01, 0x01, 0x7F, 0x01, 0x01],
    'I': [0x00, 0x41, 0x7F, 0x41, 0x00],
    ' ': [0x00, 0x00, 0x00, 0x00, 0x00],
}

def texto_a_columnas(texto):
    """Convierte texto a lista de columnas"""
    columnas = []
    for letra in texto:
        if letra.upper() in FONT:
            columnas.extend(FONT[letra.upper()])
            columnas.append(0x00)  # Espacio entre letras
    return columnas

# Configuración del SPI y MAX7219
spi = SPI(1, baudrate=10000000, polarity=0, phase=0, sck=Pin(18), mosi=Pin(23))
cs = Pin(5, Pin.OUT)

matriz = MAX7219(spi, cs)
matriz.set_brightness(5)  # Ajusta el brillo (0-15)

print("Mostrando mensaje: CETI\n")

# Preparar el mensaje
mensaje = "  CETI  "  # Espacios al inicio y final para efecto completo
columnas_mensaje = texto_a_columnas(mensaje)

# Índice de scroll
scroll_pos = 0

try:
    while True:
        # Crear buffer de 8 columnas para mostrar
        buffer = [0x00] * 8
        
        for i in range(8):
            idx = (scroll_pos + i) % len(columnas_mensaje)
            buffer[i] = columnas_mensaje[idx]
        
        # Mostrar buffer en la matriz
        matriz.display_buffer(buffer)
        
        # Avanzar posición de scroll
        scroll_pos = (scroll_pos + 1) % len(columnas_mensaje)
        
        time.sleep(0.1)  # Velocidad del scroll (ajústalo a tu gusto)

except KeyboardInterrupt:
    print("\n\nPrograma detenido")
    matriz.clear()
    print("Matriz apagada")