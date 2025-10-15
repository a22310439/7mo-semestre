#! /usr/bin/env python3
# -.- coding: utf-8 -.-

import re

# Capturar una cadena de texto
correo = input("Ingresa una dirección de correo electrónico: ")

# Función para validar correo electrónico con regex
def validar_correo(email):
    
    # Patrón regex para validar correo electrónico
    patron = r'^[a-zA-Z0-9._-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    
    # Verificar si el correo coincide con el patrón
    if re.match(patron, email):
        return True
    else:
        return False

# Validar el correo ingresado
if validar_correo(correo):
    print(f"\n'{correo}' es una dirección de correo electrónico VÁLIDA")
else:
    print(f"\n'{correo}' NO es una dirección de correo electrónico válida")
