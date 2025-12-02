from machine import Pin, ADC
import time

# Configuración del sensor de nivel de agua
sensor_agua = ADC(Pin(34))  # Pin analógico
sensor_agua.atten(ADC.ATTN_11DB)

print("=== Sensor de Nivel de Agua ===")
print("Toca las líneas del sensor con tus dedos para simular agua\n")

try:
    while True:
        nivel = sensor_agua.read()
        porcentaje = (nivel / 4095) * 100
        
        # Clasificar nivel
        if nivel < 500:
            estado = "VACÍO"
        elif nivel < 1500:
            estado = "BAJO"
        elif nivel < 2500:
            estado = "MEDIO"
        elif nivel < 3500:
            estado = "ALTO"
        else:
            estado = "LLENO"
        
        print(f"Nivel: {nivel:4d} ({porcentaje:5.1f}%) - {estado}")
        time.sleep(0.5)

except KeyboardInterrupt:
    print("\n\nPrograma detenido")