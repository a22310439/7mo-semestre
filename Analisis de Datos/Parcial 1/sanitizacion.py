import pandas as pd
import re
import os

os.chdir(r"C:\Users\CaocaoSistemas\Documents\7mo-semestre\Analisis de Datos\Parcial 1")

# Importar el CSV
data = pd.read_csv("personas.csv")

# Patrones de validación
patrones = {
    "Nombre"    : r"^[A-Z][a-zÀ-ÿ\u00f1\u00d1]*$",
    "Apellidos" : r"^[A-Z][a-zÀ-ÿ\u00f1\u00d1]*|[A-Z][a-zÀ-ÿ\u00f1\u00d1]\s[A-Z][a-zÀ-ÿ\u00f1\u00d1]$",
    "Email"     : r"^[\w\.]+@[\w\.]+\.\w+$",
    "Telefono"  : r"^\d{10}$",
    "Sexo"      : r"^(M|F)$",
    "Edad"      : r"^\d{1,3}$"
}

# Función de validación
def validar(valor, patron):
    if pd.isna(valor):
        return False
    return bool(re.match(patron, str(valor).strip()))

# Crear listas para almacenar registros válidos e inválidos
validos = []
invalidos = []

# Recorrer cada fila
for _, fila in data.iterrows():
    es_valido = True
    for col, patron in patrones.items():
        if not validar(fila[col], patron):
            es_valido = False
            break  # ya con un campo inválido no hace falta seguir
    
    if es_valido:
        validos.append(fila)
    else:
        invalidos.append(fila)

# Convertir listas a DataFrame
df_validos = pd.DataFrame(validos, columns=data.columns)
df_invalidos = pd.DataFrame(invalidos, columns=data.columns)

# Guardar en CSV sin columnas adicionales
df_validos.to_csv("validos.csv", index=False)
df_invalidos.to_csv("invalidos.csv", index=False)