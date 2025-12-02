from machine import Pin, ADC
import time

# Configuración
ldr = ADC(Pin(34))
ldr.atten(ADC.ATTN_11DB)

led = Pin(2, Pin.OUT)  # LED integrado del ESP32

# Umbral de oscuridad
UMBRAL_OSCURO = 2000  # Valores mayores = más oscuro

try:
    while True:
        valor = ldr.read()
        
        if valor > UMBRAL_OSCURO:
            # Está oscuro - encender LED
            led.value(1)
            print(f"OSCURO ({valor:4d}) → LED ENCENDIDO")
        else:
            # Hay luz - apagar LED
            led.value(0)
            print(f"LUZ ({valor:4d}) → LED APAGADO")

        time.sleep(0.5)

except KeyboardInterrupt:
    print("\n\nPrograma detenido")
    led.value(0)