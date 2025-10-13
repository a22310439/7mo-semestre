#! /usr/bin/env python3
# -.- coding: utf-8 -.-

# Capturar una cadena de texto
texto = input("Ingresa una cadena de texto: ")
print(f"\nTexto capturado: '{texto}'")

# 1. Función que verifica si la primera letra es mayúscula
def primera_mayuscula(cadena):
    if len(cadena) > 0 and cadena[0].isalpha():
        return cadena[0].isupper()
    return False

resultado1 = primera_mayuscula(texto)
print(f"\n1. ¿La primera letra es mayúscula? {resultado1}")

# 2. Función que cuenta las palabras
def contar_palabras(cadena):
    return len(cadena.split())

resultado2 = contar_palabras(texto)
print(f"\n2. Número de palabras: {resultado2}")

# 3. Función que regresa una lista con las palabras
def obtener_palabras(cadena):
    return cadena.split()

resultado3 = obtener_palabras(texto)
print(f"\n3. Lista de palabras: {resultado3}")

# 4. Función que regresa la cadena invertida
def invertir_cadena(cadena):
    return cadena[::-1]

resultado4 = invertir_cadena(texto)
print(f"\n4. Cadena invertida: '{resultado4}'")

# 5. Función que pone en mayúscula la última letra de cada palabra
def ultima_letra_mayuscula(cadena):
    palabras = cadena.split()
    palabras_modificadas = []
    
    for palabra in palabras:
        if len(palabra) > 0:
            palabra_modificada = palabra[:-1] + palabra[-1].upper()
            palabras_modificadas.append(palabra_modificada)
    
    return ' '.join(palabras_modificadas)

resultado5 = ultima_letra_mayuscula(texto)
print(f"\n5. Última letra de cada palabra en mayúscula: '{resultado5}'")