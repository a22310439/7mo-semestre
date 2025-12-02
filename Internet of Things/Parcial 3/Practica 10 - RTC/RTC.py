from machine import Pin, I2C
import time
from ds3231 import DS3231

i2c = I2C(0, scl=Pin(22), sda=Pin(21), freq=100000)
rtc = DS3231(i2c)

print("=== Reloj Digital RTC DS3231 ===\n")

dias_semana = ["Lun", "Mar", "Mié", "Jue", "Vie", "Sáb", "Dom"]

try:
    while True:
        año, mes, dia, hora, minuto, segundo, dia_sem = rtc.get_time()
        temp = rtc.get_temperature()
        
        print(f"{dias_semana[dia_sem-1]} {dia:02d}/{mes:02d}/{año}")
        print(f"{hora:02d}:{minuto:02d}:{segundo:02d}")
        print(f"{temp:.1f}°C")
        print("-" * 30)
        
        time.sleep(1)

except KeyboardInterrupt:
    print("\n\nPrograma detenido")