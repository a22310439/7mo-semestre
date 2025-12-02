from machine import Pin, I2C, SoftI2C
import ssd1306
import time
import math

# buses I2C separados
i2c_display = I2C(0, scl=Pin(25), sda=Pin(26), freq=100000)  # Bus original para el display

i2c_mpu = SoftI2C(scl=Pin(22), sda=Pin(21), freq=100000)


print("Escaneando bus I2C del display (GPIO21/22)...")
devices = i2c_display.scan()
print("Dispositivos en bus del display:", [hex(x) for x in devices])

print("\nEscaneando bus I2C del MPU...")
devices = i2c_mpu.scan()
print("Dispositivos en bus del MPU:", [hex(x) for x in devices])

# Inicializar Display en el primer bus
display = None
for addr in [0x3C, 0x3D]:
    try:
        display = ssd1306.SSD1306_I2C(128, 64, i2c_display, addr=addr)
        print(f"Display inicializado en {hex(addr)}")
        break
    except:
        pass

if display is None:
    print("ERROR: No se pudo inicializar el display!")
    raise Exception("Display no encontrado")

display.fill(0)
display.text("Iniciando...", 0, 28, 1)
display.show()

# Registros del MPU9250
PWR_MGMT_1 = 0x6B
ACCEL_XOUT_H = 0x3B
ACCEL_CONFIG = 0x1C
WHO_AM_I = 0x75

class MPU9250:
    def __init__(self, i2c, addr=None):
        self.i2c = i2c
        self.addr = addr
        
        # Auto-detectar dirección
        if self.addr is None:
            for test_addr in [0x68, 0x69]:
                try:
                    who_am_i = self.i2c.readfrom_mem(test_addr, WHO_AM_I, 1)
                    print(f"WHO_AM_I en {hex(test_addr)}: {hex(who_am_i[0])}")
                    if who_am_i[0] in [0x70, 0x71, 0x73, 0x68]:  # Variantes del MPU
                        self.addr = test_addr
                        print(f"MPU detectado en {hex(test_addr)}")
                        break
                except Exception as e:
                    print(f"No hay MPU en {hex(test_addr)}: {e}")
        
        if self.addr is None:
            raise Exception("MPU9250 no encontrado en el bus I2C")
        
        # Despertar el MPU
        try:
            self.i2c.writeto_mem(self.addr, PWR_MGMT_1, b'\x00')
            time.sleep(0.1)
            self.i2c.writeto_mem(self.addr, ACCEL_CONFIG, b'\x00')
            time.sleep(0.1)
            print("MPU9250 inicializado exitosamente")
        except Exception as e:
            raise Exception(f"Falló la inicialización del MPU: {e}")
    
    def read_accel(self):
        try:
            data = self.i2c.readfrom_mem(self.addr, ACCEL_XOUT_H, 6)
            
            accel_x = self._convert_raw(data[0], data[1]) / 16384.0
            accel_y = self._convert_raw(data[2], data[3]) / 16384.0
            accel_z = self._convert_raw(data[4], data[5]) / 16384.0
            
            return accel_x, accel_y, accel_z
        except Exception as e:
            print(f"Error leyendo acelerómetro: {e}")
            return 0, 0, 1
    
    def _convert_raw(self, high, low):
        value = (high << 8) | low
        if value > 32767:
            value -= 65536
        return value
    
    def get_angles(self):
        ax, ay, az = self.read_accel()
        roll = math.atan2(ay, az) * 180 / math.pi
        pitch = math.atan2(-ax, math.sqrt(ay*ay + az*az)) * 180 / math.pi
        return roll, pitch

class SpiritLevel:
    def __init__(self, display, width=128, height=64):
        self.display = display
        self.width = width
        self.height = height
        self.center_x = width // 2
        self.center_y = height // 2
        
    def draw_frame(self):
        self.draw_circle(self.center_x, self.center_y, 28)
        self.display.line(self.center_x - 5, self.center_y, 
                         self.center_x + 5, self.center_y, 1)
        self.display.line(self.center_x, self.center_y - 5, 
                         self.center_x, self.center_y + 5, 1)
        self.draw_circle(self.center_x, self.center_y, 5)
    
    def draw_bubble(self, roll, pitch):
        max_offset = 20
        bubble_x = int(self.center_x + (pitch * max_offset / 30))
        bubble_y = int(self.center_y + (roll * max_offset / 30))
        
        dx = bubble_x - self.center_x
        dy = bubble_y - self.center_y
        distance = math.sqrt(dx*dx + dy*dy)
        
        if distance > max_offset:
            bubble_x = int(self.center_x + (dx * max_offset / distance))
            bubble_y = int(self.center_y + (dy * max_offset / distance))
        
        self.fill_circle(bubble_x, bubble_y, 6)
        return bubble_x, bubble_y
    
    def draw_circle(self, x0, y0, r):
        x = r
        y = 0
        err = 0
        while x >= y:
            self.display.pixel(x0 + x, y0 + y, 1)
            self.display.pixel(x0 + y, y0 + x, 1)
            self.display.pixel(x0 - y, y0 + x, 1)
            self.display.pixel(x0 - x, y0 + y, 1)
            self.display.pixel(x0 - x, y0 - y, 1)
            self.display.pixel(x0 - y, y0 - x, 1)
            self.display.pixel(x0 + y, y0 - x, 1)
            self.display.pixel(x0 + x, y0 - y, 1)
            
            if err <= 0:
                y += 1
                err += 2*y + 1
            if err > 0:
                x -= 1
                err -= 2*x + 1
    
    def fill_circle(self, x0, y0, r):
        for y in range(-r, r+1):
            for x in range(-r, r+1):
                if x*x + y*y <= r*r:
                    self.display.pixel(x0 + x, y0 + y, 1)
    
    def draw_angles(self, roll, pitch):
        self.display.text("R:{:.1f}".format(roll), 0, 0, 1)
        self.display.text("P:{:.1f}".format(pitch), 70, 0, 1)
        if abs(roll) < 2 and abs(pitch) < 2:
            self.display.text("NIVEL!", 45, 56, 1)

# Programa principal
try:
    # Inicializar MPU9250 en bus separado
    mpu = MPU9250(i2c_mpu)
    spirit_level = SpiritLevel(display)
    
    display.fill(0)
    display.text("Nivel Digital", 15, 20, 1)
    display.text("Listo!", 40, 35, 1)
    display.show()
    time.sleep(1)
    
    print("Nivel digital iniciado!")
    
    while True:
        roll, pitch = mpu.get_angles()
        display.fill(0)
        spirit_level.draw_frame()
        spirit_level.draw_bubble(roll, pitch)
        spirit_level.draw_angles(roll, pitch)
        display.show()
        time.sleep(0.05)

except KeyboardInterrupt:
    print("Programa detenido")
    display.fill(0)
    display.text("Detenido", 30, 28, 1)
    display.show()
except Exception as e:
    print("Error:", e)
    display.fill(0)
    display.text("Error!", 40, 20, 1)
    display.show()
