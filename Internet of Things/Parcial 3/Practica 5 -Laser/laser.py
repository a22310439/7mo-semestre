from machine import Pin
import time

# Configuración del botón
boton = Pin(32, Pin.IN, Pin.PULL_UP)  # Botón con pull-up interno

# Configuración del módulo KY-008 (Láser)
laser = Pin(25, Pin.OUT)  # Pin de señal del láser

print("Presiona el botón para encender/apagar el láser\n")

# Variables de control
laser_encendido = False
boton_anterior = 1  # Estado anterior del botón (1 = no presionado)

# Iniciar apagado
laser.value(0)
print("Estado: APAGADO")

try:
    while True:
        # Leer estado del botón (0 = presionado, 1 = no presionado)
        boton_estado = boton.value()
        
        # Detectar flanco descendente (cuando se presiona)
        if boton_estado == 0 and boton_anterior == 1:
            # Cambiar estado del láser (toggle)
            laser_encendido = not laser_encendido
            laser.value(1 if laser_encendido else 0)
            
            if laser_encendido:
                print("Estado: ⚡ LÁSER ENCENDIDO")
            else:
                print("Estado: ⭘ LÁSER APAGADO")
            
            # Debounce - esperar a que se suelte el botón
            time.sleep(0.3)
        
        # Guardar estado anterior
        boton_anterior = boton_estado
        
        time.sleep(0.05)  # Pequeña pausa

except KeyboardInterrupt:
    print("\n\nPrograma detenido")
    laser.value(0)
    print("Láser apagado")