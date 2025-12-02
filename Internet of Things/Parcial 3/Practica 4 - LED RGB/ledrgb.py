from machine import Pin
import time

# Configuración del botón
boton = Pin(32, Pin.IN, Pin.PULL_UP)  # Botón con pull-up interno

# Configuración del LED RGB
led_red = Pin(25, Pin.OUT)
led_green = Pin(26, Pin.OUT)
led_blue = Pin(27, Pin.OUT)

def apagar_led():
    """Apaga todos los colores"""
    led_red.value(0)
    led_green.value(0)
    led_blue.value(0)

def led_rojo():
    """LED en ROJO"""
    apagar_led()
    led_red.value(1)

def led_verde():
    """LED en VERDE"""
    apagar_led()
    led_green.value(1)

def led_azul():
    """LED en AZUL"""
    apagar_led()
    led_blue.value(1)

def led_amarillo():
    """LED en AMARILLO (Rojo + Verde)"""
    apagar_led()
    led_red.value(1)
    led_green.value(1)

def led_cyan():
    """LED en CYAN (Verde + Azul)"""
    apagar_led()
    led_green.value(1)
    led_blue.value(1)

def led_magenta():
    """LED en MAGENTA (Rojo + Azul)"""
    apagar_led()
    led_red.value(1)
    led_blue.value(1)

def led_blanco():
    """LED en BLANCO (Todos)"""
    led_red.value(1)
    led_green.value(1)
    led_blue.value(1)

# Lista de colores disponibles
colores = [
    ("APAGADO", apagar_led),
    ("ROJO", led_rojo),
    ("VERDE", led_verde),
    ("AZUL", led_azul),
    ("AMARILLO", led_amarillo),
    ("CYAN", led_cyan),
    ("MAGENTA", led_magenta),
    ("BLANCO", led_blanco)
]

print("=== Control LED RGB con Botón ===")
print("Presiona el botón para cambiar de color\n")

# Variables de control
color_actual = 0
boton_anterior = 1  # Estado anterior del botón (1 = no presionado)

# Iniciar apagado
apagar_led()
print(f"Color: {colores[color_actual][0]}")

try:
    while True:
        # Leer estado del botón (0 = presionado, 1 = no presionado)
        boton_estado = boton.value()
        
        # Detectar flanco descendente (cuando se presiona)
        if boton_estado == 0 and boton_anterior == 1:
            # Avanzar al siguiente color
            color_actual = (color_actual + 1) % len(colores)
            
            # Cambiar el LED al nuevo color
            nombre_color, funcion_color = colores[color_actual]
            funcion_color()
            
            print(f"Color: {nombre_color}")
            
            # Debounce - esperar a que se suelte el botón
            time.sleep(0.3)
        
        # Guardar estado anterior
        boton_anterior = boton_estado
        
        time.sleep(0.05)  # Pequeña pausa para no saturar

except KeyboardInterrupt:
    print("\n\nPrograma detenido")
    apagar_led()
    print("LED apagado")