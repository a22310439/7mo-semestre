/*
 * Sable de Luz IoT - ESP32
 * Versión USB-Powered (bajo consumo)
 * Componentes: WS2812B (16 LEDs), MPU9250, DFPlayer Mini
 * Servidor: Blynk IoT
 */

// Configuración de Blynk (coloca tus credenciales aquí)
#define BLYNK_TEMPLATE_ID "TMPL2BaTNRQbp"
#define BLYNK_TEMPLATE_NAME "Sable de Luz"
#define BLYNK_AUTH_TOKEN "nnGIXXQV1ERfw6NbyUJV8ubZzkwvd6nu"

#define BLYNK_PRINT Serial

#include <WiFi.h>
#include <BlynkSimpleEsp32.h>
#include <FastLED.h>
#include <DFRobotDFPlayerMini.h>
#include <Wire.h>
#include <MPU9250_asukiaaa.h>

// ===== CONFIGURACIÓN WIFI =====
char ssid[] = "Wifi no disponible";
char pass[] = "Letmein!";

// ===== CONFIGURACIÓN LED STRIP =====
#define LED_PIN 12
#define NUM_LEDS 16
#define LED_TYPE WS2812B
#define COLOR_ORDER GRB
#define MAX_BRIGHTNESS 80
CRGB leds[NUM_LEDS];

// ===== CONFIGURACIÓN DFPLAYER =====
HardwareSerial dfPlayerSerial(1);
DFRobotDFPlayerMini dfPlayer;

// ===== CONFIGURACIÓN MPU9250 =====
MPU9250_asukiaaa mpu;

// ===== MODOS/PRESETS =====
enum SaberMode {
  MODE_JEDI = 0,
  MODE_SITH = 1,
  MODE_CUSTOM = 2
};

enum SoundTheme {
  SOUND_JEDI = 0,
  SOUND_SITH = 1,
  SOUND_CUSTOM = 2
};

// ===== VARIABLES DE CONTROL =====
bool saberOn = false;
SaberMode currentMode = MODE_JEDI;
SoundTheme currentSoundTheme = SOUND_JEDI;
CRGB currentColor = CRGB::Blue;
int brightness = 60;
bool customMode = false;

// Variables para detección de movimiento
float prevAccelMagnitude = 0;
unsigned long lastSwingTime = 0;
unsigned long lastClashTime = 0;

// ===== PINES =====
#define DFPLAYER_RX 16
#define DFPLAYER_TX 17

// ===== ARCHIVOS DE AUDIO (Carpeta 01) =====
// 001 - Encendido Jedi
// 002 - Apagado Jedi
// 003 - Encendido Sith
// 004 - Apagado Sith
// 005 - Zumbido en loop
// 006-009 - Swing
// 010-012 - Clash
// 013 - Canción Jedi
// 014 - Canción Sith

#define AUDIO_FOLDER 1

// ===== BLYNK VIRTUAL PINS =====
// V0 - Power (Switch ON/OFF)
// V1 - Red (0-255) - Solo activo en Custom
// V2 - Green (0-255) - Solo activo en Custom
// V3 - Blue (0-255) - Solo activo en Custom
// V4 - Preset Mode (0=Jedi, 1=Sith, 2=Custom)
// V5 - Brightness (0-80)
// V6 - Song (0=Stop, 1=Jedi, 2=Sith)
// V7 - Sound Theme (0=Jedi, 1=Sith, 2=Custom) - Solo activo en Custom

void setup() {
  Serial.begin(115200);
  
  // Inicializar WiFi y Blynk
  Blynk.begin(BLYNK_AUTH_TOKEN, ssid, pass);
  Serial.println("Conectando a Blynk...");
  
  // Inicializar LED Strip
  FastLED.addLeds<LED_TYPE, LED_PIN, COLOR_ORDER>(leds, NUM_LEDS);
  FastLED.setMaxPowerInVoltsAndMilliamps(5, 350);
  FastLED.setBrightness(brightness);
  FastLED.clear();
  FastLED.show();
  Serial.println("LED Strip inicializado");
  
  // Inicializar DFPlayer
  dfPlayerSerial.begin(9600, SERIAL_8N1, DFPLAYER_RX, DFPLAYER_TX);
  delay(500);
  
  if (!dfPlayer.begin(dfPlayerSerial)) {
    Serial.println("Error al inicializar DFPlayer!");
    Serial.println("Verifica:");
    Serial.println("1. Conexiones RX/TX");
    Serial.println("2. MicroSD insertada y formateada FAT32");
    Serial.println("3. Archivos en carpeta /01/");
  } else {
    Serial.println("DFPlayer inicializado correctamente");
    dfPlayer.volume(25);  // Volumen 0-30
    delay(100);
  }
  
  // Inicializar MPU9250
  Wire.begin();
  mpu.setWire(&Wire);
  mpu.beginAccel();
  mpu.beginGyro();
  Serial.println("MPU9250 inicializado");
  
  // Aplicar preset inicial (Jedi)
  applyPreset(MODE_JEDI);
  
  delay(1000);
}

void loop() {
  Blynk.run();
  
  if (saberOn) {
    checkMotion();
    updateLEDs();
  }
  
  delay(10);
}

// ===== FUNCIONES DE PRESETS =====

void applyPreset(SaberMode mode) {
  currentMode = mode;
  bool wasOn = saberOn;

  switch(mode) {
    case MODE_JEDI:
      currentColor = CRGB(0, 0, 255);  // Azul
      currentSoundTheme = SOUND_JEDI;
      customMode = false;
      Serial.println("Preset aplicado: JEDI (Azul)");

      Blynk.virtualWrite(V1, 0);    // Red
      Blynk.virtualWrite(V2, 0);    // Green
      Blynk.virtualWrite(V3, 255);  // Blue
      Blynk.virtualWrite(V7, 0);    // Sound Theme Jedi
      break;

    case MODE_SITH:
      currentColor = CRGB(255, 0, 0);  // Rojo
      currentSoundTheme = SOUND_SITH;
      customMode = false;
      Serial.println("Preset aplicado: SITH (Rojo)");

      Blynk.virtualWrite(V1, 255);  // Red
      Blynk.virtualWrite(V2, 0);    // Green
      Blynk.virtualWrite(V3, 0);    // Blue
      Blynk.virtualWrite(V7, 1);    // Sound Theme Sith
      break;

    case MODE_CUSTOM:
      customMode = true;
      Serial.println("Modo CUSTOM activado");
      break;
  }

  if (wasOn) {
    dfPlayer.stop();
    delay(100);
    
    // Reproducir sonido de encendido del nuevo preset
    if (currentSoundTheme == SOUND_JEDI) {
      dfPlayer.playFolder(AUDIO_FOLDER, 1);  // 001 - Encendido Jedi
      Serial.println("Reproduciendo: 01/001 - Encendido Jedi");
    } else if (currentSoundTheme == SOUND_SITH) {
      dfPlayer.playFolder(AUDIO_FOLDER, 3);  // 003 - Encendido Sith
      Serial.println("Reproduciendo: 01/003 - Encendido Sith");
    }

    updateLEDs();
    
    // Esperar e iniciar zumbido
    delay(2000);
    dfPlayer.playFolder(AUDIO_FOLDER, 5);  // 005 - Zumbido
    dfPlayer.enableLoop();
    Serial.println("Zumbido iniciado: 01/005");
  }
}

// ===== FUNCIONES BLYNK =====

BLYNK_WRITE(V0) {
  int value = param.asInt();
  
  if (value == 1 && !saberOn) {
    saberOn = true;
    turnOnSaber();
  } else if (value == 0 && saberOn) {
    saberOn = false;
    turnOffSaber();
  }
}

BLYNK_WRITE(V1) {
  if (customMode) {
    int r = param.asInt();
    currentColor.r = r;
    Serial.printf("Custom - Rojo: %d\n", r);
  } else {
    Serial.println("Cambio de color bloqueado - Cambia a modo Custom");
  }
}

BLYNK_WRITE(V2) {
  if (customMode) {
    int g = param.asInt();
    currentColor.g = g;
    Serial.printf("Custom - Verde: %d\n", g);
  } else {
    Serial.println("Cambio de color bloqueado - Cambia a modo Custom");
  }
}

BLYNK_WRITE(V3) {
  if (customMode) {
    int b = param.asInt();
    currentColor.b = b;
    Serial.printf("Custom - Azul: %d\n", b);
  } else {
    Serial.println("Cambio de color bloqueado - Cambia a modo Custom");
  }
}

BLYNK_WRITE(V4) {
  int modeValue = param.asInt();
  
  if (modeValue >= 0 && modeValue <= 2) {
    applyPreset((SaberMode)(modeValue));
  }
}

BLYNK_WRITE(V5) {
  brightness = constrain(param.asInt(), 0, MAX_BRIGHTNESS);
  FastLED.setBrightness(brightness);
  Serial.printf("Brillo: %d\n", brightness);
}

BLYNK_WRITE(V6) {
  int songNumber = param.asInt();
  
  if (songNumber == 0) {
    dfPlayer.stop();
    Serial.println("Música detenida");
  } else if (songNumber == 1) {
    dfPlayer.playFolder(AUDIO_FOLDER, 13);  // 013 - Tema Jedi
    dfPlayer.enableLoop();
    Serial.println("Reproduciendo: 01/013 - Tema Jedi (loop)");
  } else if (songNumber == 2) {
    dfPlayer.playFolder(AUDIO_FOLDER, 14);  // 014 - Tema Sith
    dfPlayer.enableLoop();
    Serial.println("Reproduciendo: 01/014 - Tema Sith (loop)");
  }
}

BLYNK_WRITE(V7) {
  if (customMode) {
    int themeValue = param.asInt();
    
    if (themeValue >= 0 && themeValue <= 2) {
      currentSoundTheme = (SoundTheme)themeValue;
      
      if (currentSoundTheme == SOUND_JEDI) {
        Serial.println("Tema de sonido: JEDI");
      } else if (currentSoundTheme == SOUND_SITH) {
        Serial.println("Tema de sonido: SITH");
      } else {
        Serial.println("Tema de sonido: CUSTOM");
      }
    }
  } else {
    Serial.println("Cambio de sonido bloqueado - Cambia a modo Custom");
  }
}

// ===== FUNCIONES DEL SABLE =====

void turnOnSaber() {
  Serial.println("=== Encendiendo sable ===");
  
  // Limpiar estado del DFPlayer
  dfPlayer.stop();
  dfPlayer.disableLoop();
  delay(200);
  
  // Sonido de encendido según el tema
  if (currentSoundTheme == SOUND_JEDI) {
    dfPlayer.playFolder(AUDIO_FOLDER, 1);  // 001 - Encendido Jedi
    Serial.println("Reproduciendo: 01/001 - Encendido Jedi");
  } else if (currentSoundTheme == SOUND_SITH) {
    dfPlayer.playFolder(AUDIO_FOLDER, 3);  // 003 - Encendido Sith
    Serial.println("Reproduciendo: 01/003 - Encendido Sith");
  } else {
    dfPlayer.playFolder(AUDIO_FOLDER, 1);  // Default: Jedi
    Serial.println("Reproduciendo: 01/001 - Encendido Jedi (default)");
  }

  delay(500);

  // Efecto de LEDs primero
  for (int i = 0; i < NUM_LEDS; i++) {
    leds[i] = currentColor;
    FastLED.show();
    delay(10);
  }
  
  // Esperar a que termine el sonido de encendido
  delay(1500);  // Ajusta según la duración de tus archivos
  
  // Iniciar zumbido en loop
  Serial.println("Iniciando zumbido...");
  dfPlayer.playFolder(AUDIO_FOLDER, 5);  // 005 - Zumbido
  delay(100);
  dfPlayer.enableLoop();
  Serial.println("Zumbido en loop: 01/005");
  
  Serial.println("=== Sable encendido ===");
}

void turnOffSaber() {
  Serial.println("=== Apagando sable ===");

  // Detener zumbido
  dfPlayer.stop();
  dfPlayer.disableLoop();
  delay(200);

  // Sonido de apagado
  if (currentSoundTheme == SOUND_JEDI) {
    dfPlayer.playFolder(AUDIO_FOLDER, 2);  // 002 - Apagado Jedi
    Serial.println("Reproduciendo: 01/002 - Apagado Jedi");
  } else if (currentSoundTheme == SOUND_SITH) {
    dfPlayer.playFolder(AUDIO_FOLDER, 4);  // 004 - Apagado Sith
    Serial.println("Reproduciendo: 01/004 - Apagado Sith");
  } else {
    dfPlayer.playFolder(AUDIO_FOLDER, 2);  // Default: Jedi
    Serial.println("Reproduciendo: 01/002 - Apagado Jedi (default)");
  }

  delay(1000);

  // Efecto de apagado de LEDs
  for (int i = NUM_LEDS - 1; i >= 0; i--) {
    leds[i] = CRGB::Black;
    FastLED.show();
    delay(10);
  }

  delay(1000);
  dfPlayer.stop();

  Serial.println("=== Sable apagado ===");
}

void updateLEDs() {
  fill_solid(leds, NUM_LEDS, currentColor);
  FastLED.show();
}

void checkMotion() {
  if (mpu.accelUpdate() == 0) {
    float aX = mpu.accelX();
    float aY = mpu.accelY();
    float aZ = mpu.accelZ();
    
    float accelMagnitude = sqrt(aX * aX + aY * aY + aZ * aZ);
    float accelChange = abs(accelMagnitude - prevAccelMagnitude);
    
    unsigned long currentTime = millis();
    
    // Detectar swing
    if (accelChange > 5.0 && (currentTime - lastSwingTime) > 300) {
      playSwingSound();
      lastSwingTime = currentTime;
    }
    
    // Detectar clash
    if (accelChange > 12.0 && (currentTime - lastClashTime) > 500) {
      playClashSound();
      flashEffect();
      lastClashTime = currentTime;
    }
    
    prevAccelMagnitude = accelMagnitude;
  }
}

void playSwingSound() {
  // Archivos 006-009 para swings
  int soundFile = 6 + random(0, 4);
  
  // Pausar zumbido
  dfPlayer.pause();
  delay(50);
  
  // Reproducir swing
  dfPlayer.playFolder(AUDIO_FOLDER, soundFile);
  Serial.printf("Swing! 01/%03d\n", soundFile);
  
  // Reanudar zumbido
  delay(500);
  dfPlayer.start();
}

void playClashSound() {
  // Archivos 010-012 para clash
  int soundFile = 10 + random(0, 3);
  
  // Pausar zumbido
  dfPlayer.pause();
  delay(50);
  
  // Reproducir clash
  dfPlayer.playFolder(AUDIO_FOLDER, soundFile);
  Serial.printf("Clash! 01/%03d\n", soundFile);
  
  // Reanudar zumbido
  delay(600);
  dfPlayer.start();
}

void flashEffect() {
  CRGB originalColor = currentColor;
  
  for (int i = 0; i < 2; i++) {
    fill_solid(leds, NUM_LEDS, CRGB::White);
    FastLED.show();
    delay(40);
    fill_solid(leds, NUM_LEDS, originalColor);
    FastLED.show();
    delay(40);
  }
}