#! /usr/bin/env python3
# -.- coding: utf-8 -.-

# Capturar una cadena de texto
correo = input("Ingresa una dirección de correo electrónico: ")

# Función para validar correo electrónico
def validar_correo(email):
    """
    Valida si una cadena es una dirección de correo electrónico válida.
    Criterios de validación:
    - Debe contener exactamente un símbolo @
    - Debe tener texto antes del @
    - Debe tener texto después del @
    - Debe contener al menos un punto después del @
    - El dominio debe tener al menos 2 caracteres después del último punto
    - No debe contener espacios
    """
    
    # Eliminar espacios en blanco al inicio y final
    email = email.strip()
    
    # Verificar que no contenga espacios
    if ' ' in email:
        return False
    
    # Verificar que contenga exactamente un @
    if email.count('@') != 1:
        return False
    
    # Dividir en usuario y dominio
    partes = email.split('@')
    usuario = partes[0]
    dominio = partes[1]
    
    # Verificar que el usuario no esté vacío
    if len(usuario) == 0:
        return False
    
    # Verificar que el dominio no esté vacío
    if len(dominio) == 0:
        return False
    
    # Verificar que el dominio contenga al menos un punto
    if '.' not in dominio:
        return False
    
    # Verificar que el punto no esté al inicio o final del dominio
    if dominio.startswith('.') or dominio.endswith('.'):
        return False
    
    # Verificar que haya al menos 2 caracteres después del último punto
    ultima_parte = dominio.split('.')[-1]
    if len(ultima_parte) < 2:
        return False
    
    # Verificar que no haya puntos consecutivos
    if '..' in dominio:
        return False
    
    # Verificar que el usuario no comience o termine con punto
    if usuario.startswith('.') or usuario.endswith('.'):
        return False
    
    return True

# Validar el correo ingresado
if validar_correo(correo):
    print(f"\n✓ '{correo}' es una dirección de correo electrónico VÁLIDA")
else:
    print(f"\n✗ '{correo}' NO es una dirección de correo electrónico válida")

# Ejemplos de prueba
print("\n--- Ejemplos de prueba ---")
ejemplos = [
    "usuario@ejemplo.com",
    "nombre.apellido@empresa.com.mx",
    "correo@dominio",
    "@ejemplo.com",
    "usuario@",
    "usuario ejemplo@correo.com",
    "usuario@@correo.com",
    "usuario@.com",
    "usuario@dominio.",
    ".usuario@dominio.com",
    "usuario.@dominio.com",
    "usuario@dominio..com"
]

for ejemplo in ejemplos:
    resultado = "VÁLIDO" if validar_correo(ejemplo) else "NO VÁLIDO"
    print(f"{ejemplo:35} -> {resultado}")