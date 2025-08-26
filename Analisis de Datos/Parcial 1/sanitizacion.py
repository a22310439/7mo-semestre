import pandas as pd
import re
import os

# Importar el CSV
data = pd.read_csv("personas.csv")

# Patrones de validacion
patrones = {
    "Nombre"    : r"^([A-Z][a-zÀ-ÿ\u00f1\u00d1]*\s?){1,2}$",
    "Apellidos" : r"^([A-Z][a-zÀ-ÿ\u00f1\u00d1]*\s?){1,2}$",
    "Email"     : r"^[\w\.]+@[\w\.]+\.\w+$",
    "Telefono"  : r"^\d{10}$",
    "Sexo"      : r"^(M|F)$",
    "Edad"      : r"^\d{1,3}$"
}

# Funcion de validacion
def validar(valor, patron):
    if pd.isna(valor):
        return False
    return bool(re.match(patron, str(valor).strip()))

# Crear listas para almacenar registros validos e invalidos
validos = []
invalidos = []

# Recorrer cada fila
for _, fila in data.iterrows():
    es_valido = True
    for col, patron in patrones.items():
        if not validar(fila[col], patron):
            es_valido = False
            break
    
    if es_valido:
        validos.append(fila)
    else:
        invalidos.append(fila)

# Convertir listas a DataFrame
df_validos = pd.DataFrame(validos, columns=data.columns)
df_invalidos = pd.DataFrame(invalidos, columns=data.columns)

# Guardar en CSV
df_validos.to_csv("validos.csv", index=False)
df_invalidos.to_csv("invalidos.csv", index=False)