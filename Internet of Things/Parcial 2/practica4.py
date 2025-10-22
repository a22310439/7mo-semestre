#! /usr/bin/env python3
# -.- coding: utf-8 -.-

import csv
from datetime import date, datetime
import os

# === CONFIGURACIÓN ===
ARCHIVO_INFO = "res/info.csv"
ARCHIVO_PLANTILLA = "res/oficio.txt"
CARPETA_SALIDA = "constancias"

# === FUNCIONES AUXILIARES ===

def calcular_edad(fecha_nacimiento):
    """Calcula la edad a partir de una fecha de nacimiento (YYYY-MM-DD)."""
    nacimiento = datetime.strptime(fecha_nacimiento, "%Y-%m-%d").date()
    hoy = date.today()
    edad = hoy.year - nacimiento.year - ((hoy.month, hoy.day) < (nacimiento.month, nacimiento.day))
    return edad

def fecha_actual_formateada():
    """Devuelve la fecha actual en formato: '21 de octubre de 2025'."""
    meses = [
        "enero", "febrero", "marzo", "abril", "mayo", "junio",
        "julio", "agosto", "septiembre", "octubre", "noviembre", "diciembre"
    ]
    hoy = date.today()
    return f"{hoy.day} de {meses[hoy.month - 1]} de {hoy.year}"

# === PROCESO PRINCIPAL ===

def main():
    # Crear carpeta de salida si no existe
    os.makedirs(CARPETA_SALIDA, exist_ok=True)

    # Cargar plantilla del oficio
    with open(ARCHIVO_PLANTILLA, "r", encoding="utf-8") as f:
        plantilla = f.read()

    # Leer datos del CSV
    with open(ARCHIVO_INFO, "r", encoding="utf-8") as f:
        lector = csv.DictReader(f)
        for persona in lector:
            # Calcular edad
            persona["edad"] = calcular_edad(persona["fechaNacimiento"])
            persona["fechaActual"] = fecha_actual_formateada()

            # Si no hay número interior, se omite
            numero_int = persona["numeroInt"].strip()
            persona["numeroIntTexto"] = f" Int. {numero_int}" if numero_int else ""

            # Reemplazar los campos en la plantilla
            oficio_texto = plantilla.format(**persona)

            # Nombre del archivo de salida
            nombre_archivo = f"oficio_{persona['registro']}.txt"
            ruta_salida = os.path.join(CARPETA_SALIDA, nombre_archivo)

            # Guardar el oficio generado
            with open(ruta_salida, "w", encoding="utf-8") as salida:
                salida.write(oficio_texto)

            print(f"✅ Constancia generada: {nombre_archivo}")

if __name__ == "__main__":
    main()
