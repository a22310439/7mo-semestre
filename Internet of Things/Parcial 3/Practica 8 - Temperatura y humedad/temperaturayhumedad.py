from machine import Pin
import dht
import time

# Configuración del DHT11
sensor = dht.DHT11(Pin(15))  # Conectar DATA a GPIO15

try:
    while True:
        try:
            # Leer sensor
            sensor.measure()
            temperatura = sensor.temperature()
            humedad = sensor.humidity()
            
            print(f"Temperatura: {temperatura}°C")
            print(f"Humedad: {humedad}%")
            print("-" * 30)
            
            time.sleep(2)
            
        except OSError as e:
            print(f"Error leyendo sensor: {e}")
            time.sleep(2)

except KeyboardInterrupt:
    print("\n\nPrograma detenido")