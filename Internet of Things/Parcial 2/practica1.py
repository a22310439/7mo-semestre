#! /usr/bin/env python3
# -.- coding: utf-8 -.-

# Capturar varios números y almacenarlos en una lista
numeros = []
print("Ingresa números (escribe 'fin' para terminar):")

while True:
    entrada = input("Número: ")
    if entrada.lower() == 'fin':
        break
    try:
        numeros.append(int(entrada))
    except ValueError:
        print("Por favor ingresa un número válido")

print(f"\nLista original: {numeros}")

# 1. Sublista de 2 elementos correspondiente a la mitad de la lista
mitad = len(numeros) // 2
sublista_mitad = numeros[mitad:mitad+2]
print(f"\n1. Sublista de 2 elementos en la mitad: {sublista_mitad}")

# 2. Imprimir primer y último elemento en una sola línea
print(f"\n2. Primer y último elemento: {numeros[0]}, {numeros[-1]}")

# 3. Agregar los elementos de la lista al final de la misma
numeros.extend(numeros.copy())
print(f"\n3. Lista duplicada: {numeros}")

# 4. Ordenar de menor a mayor
numeros.sort()
print(f"\n4. Lista ordenada de menor a mayor: {numeros}")

# 5. Ordenar de mayor a menor
print(f"\n5. Lista ordenada de mayor a menor: {numeros.sort(reverse=True) or numeros}")

# 6. Función que devuelve el cubo de los elementos
def cubo_elementos(lista):
    return [x**3 for x in lista]

lista_cubos = cubo_elementos(numeros)
print(f"\n6. Cubos de los elementos: {lista_cubos}")