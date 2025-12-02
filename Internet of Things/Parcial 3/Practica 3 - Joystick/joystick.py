from machine import Pin, I2C, ADC, UART
import ssd1306
import time
import math

# Crear bus I2C para display
i2c_display = I2C(0, scl=Pin(25), sda=Pin(26), freq=100000)

print("Escaneando bus I2C del display (GPIO25/26)...")
devices = i2c_display.scan()
print("Dispositivos en bus del display:", [hex(x) for x in devices])

# Inicializar Display
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

class JoystickReader:
    def __init__(self, x_pin, y_pin, sw_pin):
        """
        Inicializa el joystick
        x_pin, y_pin: pines ADC para los ejes X e Y
        sw_pin: pin digital para el botón (switch)
        """
        # Configurar ADCs para los ejes (lectura 0-4095 en ESP32)
        self.adc_x = ADC(Pin(x_pin))
        self.adc_y = ADC(Pin(y_pin))
        
        # Configurar atenuación para rango completo 0-3.3V
        self.adc_x.atten(ADC.ATTN_11DB)
        self.adc_y.atten(ADC.ATTN_11DB)
        
        # Configurar botón con pull-up interno
        self.button = Pin(sw_pin, Pin.IN, Pin.PULL_UP)
        
        # Calibración del centro (se hará al inicio)
        self.center_x = 2048  # Valor medio teórico
        self.center_y = 2048
        self.calibrated = False
        
        # Zona muerta para evitar drift
        self.deadzone = 100
        
        print("Joystick inicializado")
        print("Presiona el botón del joystick para calibrar...")
    
    def calibrate(self):
        """Calibra el centro del joystick"""
        # Tomar varias lecturas para promediar
        samples = 10
        sum_x = 0
        sum_y = 0
        
        for _ in range(samples):
            sum_x += self.adc_x.read()
            sum_y += self.adc_y.read()
            time.sleep(0.01)
        
        self.center_x = sum_x // samples
        self.center_y = sum_y // samples
        self.calibrated = True
        
        print(f"Calibración completada: Centro X={self.center_x}, Y={self.center_y}")
    
    def read_position(self):
        """
        Lee la posición del joystick y la convierte a ángulos
        Retorna (roll, pitch) en grados, similar al acelerómetro
        """
        # Leer valores RAW
        raw_x = self.adc_x.read()
        raw_y = self.adc_y.read()
        
        # Calcular desviación del centro
        delta_x = raw_x - self.center_x
        delta_y = raw_y - self.center_y
        
        # Aplicar zona muerta
        if abs(delta_x) < self.deadzone:
            delta_x = 0
        if abs(delta_y) < self.deadzone:
            delta_y = 0
        
        # Convertir a ángulos (-30° a +30° aproximadamente)
        # El rango del ADC es ~2048 desde el centro
        max_range = 2048 - self.deadzone
        
        # Mapear a ángulos (invertir Y si es necesario)
        pitch = (delta_x / max_range) * 30  # Eje X → Pitch
        roll = (-delta_y / max_range) * 30   # Eje Y → Roll (invertido)
        
        # Limitar ángulos
        pitch = max(-30, min(30, pitch))
        roll = max(-30, min(30, roll))
        
        return roll, pitch
    
    def is_button_pressed(self):
        """Verifica si el botón está presionado (activo bajo)"""
        return self.button.value() == 0
    
    def get_raw_values(self):
        """Retorna valores RAW para debugging"""
        return self.adc_x.read(), self.adc_y.read()

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
            self.display.text("CENTRO!", 40, 56, 1)

# Programa principal
try:
    # Configuración de pines del joystick
    JOYSTICK_X_PIN = 34  # Pin ADC para eje X
    JOYSTICK_Y_PIN = 35  # Pin ADC para eje Y
    JOYSTICK_SW_PIN = 32 # Pin digital para botón
    
    joystick = JoystickReader(JOYSTICK_X_PIN, JOYSTICK_Y_PIN, JOYSTICK_SW_PIN)
    spirit_level = SpiritLevel(display)
    
    display.fill(0)
    display.text("Nivel Joystick", 10, 15, 1)
    display.text("+ RFID", 40, 30, 1)
    display.text("Presiona boton", 5, 45, 1)
    display.text("para calibrar", 10, 55, 1)
    display.show()
    time.sleep(2)
    
    # Esperar calibración inicial
    while not joystick.calibrated:
        if joystick.is_button_pressed():
            joystick.calibrate()
            display.fill(0)
            display.text("Calibrado!", 25, 28, 1)
            display.show()
            time.sleep(1)
            break
        time.sleep(0.1)
    
    # Si no se calibró, usar valores por defecto
    if not joystick.calibrated:
        print("Usando calibración por defecto")
        joystick.calibrated = True
    
    print("Sistema iniciado - Nivel Joystick + RFID")
    button_pressed_last = False
    
    while True:
        # Detectar presión del botón para recalibrar
        button_pressed = joystick.is_button_pressed()
        if button_pressed and not button_pressed_last:
            print("Recalibrando joystick...")
            display.fill(0)
            display.text("Recalibrando..", 10, 28, 1)
            display.show()
            time.sleep(0.5)
            joystick.calibrate()
        button_pressed_last = button_pressed
        
        # Actualizar nivel con joystick
        roll, pitch = joystick.read_position()
        
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
    import sys
    sys.print_exception(e)
    display.fill(0)
    display.text("Error!", 40, 20, 1)
    display.show()