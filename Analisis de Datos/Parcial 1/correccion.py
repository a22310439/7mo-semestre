import ttkbootstrap as ttk
from ttkbootstrap.constants import *
from ttkbootstrap.dialogs import Messagebox
import pandas as pd
import re
import os
from pandas.errors import EmptyDataError

# -------------------------------
# Configuración de archivos
# -------------------------------
FILE_INVALIDOS = "invalidos.csv"
FILE_VALIDOS = "validos.csv"

# -------------------------------
# Patrones de validación
# -------------------------------
patrones = {
    "Nombre": r"^[A-Z][a-zÀ-ÿ\u00f1\u00d1]*(\s[A-Z][a-zÀ-ÿ\u00f1\u00d1]*)?$",
    "Apellidos": r"^[A-Z][a-zÀ-ÿ\u00f1\u00d1]*(\s[A-Z][a-zÀ-ÿ\u00f1\u00d1]*)?$",
    "Email": r"^[\w\.-]+@[\w\.-]+\.\w+$",
    "Telefono": r"^\d{10}$",
    "Sexo": r"^(M|F)$",
    "Edad": r"^\d{1,3}$"
}

# Columnas esperadas (las 6 principales + Datos extra)
COLUMNAS_PRINCIPALES = ["Nombre", "Apellidos", "Email", "Telefono", "Sexo", "Edad"]
COLUMNA_DATOS_EXTRA = "Datos extra"
COLUMNAS_ESPERADAS = COLUMNAS_PRINCIPALES + [COLUMNA_DATOS_EXTRA]

def validar(valor, patron):
    """Valida un campo contra un patrón regex"""
    return bool(re.match(patron, str(valor).strip())) if pd.notna(valor) else False

def leer_csv_flexible(filepath):
    """
    Lee un CSV que puede tener filas con diferente número de columnas
    """
    import csv
    
    # Leer todas las líneas del archivo
    with open(filepath, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    
    if not lines:
        return pd.DataFrame(columns=COLUMNAS_ESPERADAS)
    
    # Obtener los headers de la primera línea
    headers = lines[0].strip().split(',')
    
    # Procesar cada línea
    data = []
    for i, line in enumerate(lines[1:], 1):  # Empezar desde la línea 1 (skip header)
        if not line.strip():
            continue
            
        # Usar csv.reader para manejar correctamente las comillas y comas
        row_data = next(csv.reader([line]))
        
        # Si la fila tiene exactamente el número correcto de columnas
        if len(row_data) == len(headers):
            row_dict = dict(zip(headers, row_data))
        
        # Si la fila tiene más columnas de las esperadas
        elif len(row_data) > len(headers):
            row_dict = {}
            
            # Asignar los valores a las columnas conocidas
            for j, header in enumerate(headers[:6]):  # Las primeras 6 columnas principales
                row_dict[header] = row_data[j] if j < len(row_data) else ""
            
            # Concatenar todos los valores extras
            extras = []
            
            # Si había una columna "Datos extra" original, incluir su valor
            if len(headers) > 6 and len(row_data) > 6:
                if row_data[6]:  # El valor original de "Datos extra"
                    extras.append(row_data[6])
            
            # Agregar todos los valores adicionales
            for j in range(7, len(row_data)):
                if row_data[j] and row_data[j].strip():
                    extras.append(row_data[j].strip())
            
            # Unir todos los extras
            row_dict[COLUMNA_DATOS_EXTRA] = " | ".join(extras) if extras else ""
        
        # Si la fila tiene menos columnas
        else:
            row_dict = dict(zip(headers, row_data + [''] * (len(headers) - len(row_data))))
        
        data.append(row_dict)
    
    # Crear DataFrame
    df = pd.DataFrame(data)
    
    # Asegurar que todas las columnas principales existen
    for col in COLUMNAS_PRINCIPALES:
        if col not in df.columns:
            df[col] = ""
    
    # Si no existe la columna de datos extra pero hay datos para ella, crearla
    if COLUMNA_DATOS_EXTRA not in df.columns:
        df[COLUMNA_DATOS_EXTRA] = ""
    
    return df

def procesar_datos_extra(df):
    if df.empty:
        return df
    
    # Limpiar nombres de columnas
    df.columns = df.columns.str.strip()
    
    # Crear un nuevo DataFrame con las columnas correctas
    df_procesado = pd.DataFrame()
    
    # Copiar las columnas principales
    for col in COLUMNAS_PRINCIPALES:
        if col in df.columns:
            df_procesado[col] = df[col].fillna("")
        else:
            df_procesado[col] = ""
    
    # Identificar si hay columnas extras (que no sean las principales ni "Datos extra")
    columnas_extras = [col for col in df.columns 
                      if col not in COLUMNAS_PRINCIPALES and col != COLUMNA_DATOS_EXTRA]
    
    # Procesar datos extra
    datos_extra_final = []
    
    for idx, row in df.iterrows():
        extras = []
        
        # Si existe la columna "Datos extra" original, incluir su valor
        if COLUMNA_DATOS_EXTRA in df.columns:
            val = row[COLUMNA_DATOS_EXTRA]
            if pd.notna(val) and str(val).strip() and str(val).strip() != 'nan':
                extras.append(str(val).strip())
        
        # Agregar valores de columnas extras
        for col in columnas_extras:
            val = row[col]
            if pd.notna(val) and str(val).strip() and str(val).strip() != 'nan':
                # Si la columna tiene un nombre significativo, incluirlo
                if not col.startswith('Unnamed:') and not col.startswith('ExtraCol_'):
                    extras.append(f"{col}: {val}")
                else:
                    extras.append(str(val).strip())
        
        datos_extra_final.append(" | ".join(extras) if extras else "")
    
    # Solo agregar la columna de datos extra si hay algún valor
    if any(dato.strip() for dato in datos_extra_final):
        df_procesado[COLUMNA_DATOS_EXTRA] = datos_extra_final
    
    return df_procesado

# -------------------------------
# UI principal
# -------------------------------
root = ttk.Window(themename="darkly")
root.title("Editor de Registros Inválidos")
root.geometry("1200x550")

# Marco principal con tabla + scrollbar
frame = ttk.Frame(root)
frame.pack(fill=BOTH, expand=True, padx=10, pady=10)

tree = ttk.Treeview(frame, show="headings", bootstyle="info table")
tree.pack(side=LEFT, fill=BOTH, expand=True)

scroll = ttk.Scrollbar(frame, command=tree.yview, orient="vertical")
scroll.pack(side=RIGHT, fill=Y)
tree.configure(yscrollcommand=scroll.set)

# Barra de estado
status_var = ttk.StringVar(value="Listo")
status_bar = ttk.Label(root, textvariable=status_var, anchor="w", bootstyle="secondary")
status_bar.pack(fill=X, side=BOTTOM)

def update_status(msg):
    status_var.set(msg)

# -------------------------------
# Funciones auxiliares
# -------------------------------
def cargar_tabla(df):
    """Carga el DataFrame en el Treeview"""
    tree.delete(*tree.get_children())
    tree["columns"] = list(df.columns)

    # Configurar encabezados y tamaño dinámico
    for col in df.columns:
        tree.heading(col, text=col)
        # Ajustar ancho a contenido más largo
        if col == COLUMNA_DATOS_EXTRA:
            # Dar más espacio a la columna de datos extra
            tree.column(col, width=200, anchor="center")
        else:
            max_len = max([len(str(val)) for val in df[col].values] + [len(col)]) * 10
            tree.column(col, width=max_len, anchor="center")

    # Insertar filas con indicación de campos erróneos
    for _, row in df.iterrows():
        values = []
        for col in df.columns:
            val = row[col]
            
            # Convertir NaN a cadena vacía
            if pd.isna(val) or str(val).lower() == 'nan':
                val = ""
            
            # Si el campo es inválido, agregar un indicador visual
            if col in patrones and not validar(val, patrones[col]) and val != "":
                values.append(f"❌ {val}")
            else:
                values.append(val)
        
        tree.insert("", "end", values=values)

def update_invalidos_file():
    """Guarda el estado actual del Treeview en invalidos.csv"""
    invalid_rows = []
    tiene_datos_extra = False
    
    for item in tree.get_children():
        values = tree.item(item)["values"]
        # Limpiar los indicadores ❌ antes de guardar
        cleaned_values = []
        for val in values:
            if isinstance(val, str) and val.startswith("❌ "):
                cleaned_values.append(val[2:])  # Remover "❌ "
            else:
                cleaned_values.append(val)
        
        row_dict = dict(zip(tree["columns"], cleaned_values))
        
        # Verificar si hay datos extra en esta fila
        if COLUMNA_DATOS_EXTRA in row_dict and row_dict[COLUMNA_DATOS_EXTRA].strip():
            tiene_datos_extra = True
        
        invalid_rows.append(row_dict)

    if invalid_rows:
        df = pd.DataFrame(invalid_rows)
        
        # Si no hay datos extra en ninguna fila, eliminar la columna antes de guardar
        if COLUMNA_DATOS_EXTRA in df.columns and not tiene_datos_extra:
            df = df.drop(columns=[COLUMNA_DATOS_EXTRA])
        
        df.to_csv(FILE_INVALIDOS, index=False)
    else:
        # Crear archivo vacío solo con las columnas principales
        pd.DataFrame(columns=COLUMNAS_PRINCIPALES).to_csv(FILE_INVALIDOS, index=False)

def edit_row(item):
    """Abre ventana para editar una fila"""
    old_values = tree.item(item)["values"]
    
    # Limpiar valores de indicadores ❌ y nan
    cleaned_values = []
    for val in old_values:
        if isinstance(val, str) and val.startswith("❌ "):
            cleaned_val = val[2:]
        else:
            cleaned_val = val
        
        # Convertir nan a cadena vacía
        if pd.isna(cleaned_val) or str(cleaned_val).lower() == 'nan' or str(cleaned_val) == '':
            cleaned_values.append("")
        else:
            cleaned_values.append(cleaned_val)
    
    edit_win = ttk.Toplevel(root)
    edit_win.title("Editar fila")
    
    # Prevenir que se muestre la X (botón de cerrar) en la ventana
    edit_win.resizable(False, False)
    edit_win.grab_set()  # Hacer la ventana modal
    
    entries = {}
    entry_frames = {}
    
    # Variable para el checkbox
    mantener_datos_extra = ttk.BooleanVar(value=False)

    # Validar campos iniciales para marcar en rojo
    def validate_field(col, value):
        if col in patrones:
            return validar(value, patrones[col])
        return True

    # Función para actualizar el color del campo
    def update_field_color(col, entry):
        value = entry.get()
        if validate_field(col, value):
            entry.configure(bootstyle="default")
        else:
            entry.configure(bootstyle="danger")

    # Crear campos de entrada
    for idx, col in enumerate(tree["columns"]):
        # Frame para cada campo
        field_frame = ttk.Frame(edit_win)
        field_frame.grid(row=idx, column=0, columnspan=2, padx=5, pady=5, sticky="ew")
        entry_frames[col] = field_frame
        
        # Label
        ttk.Label(field_frame, text=col, width=15).pack(side=LEFT, padx=(0, 5))
        
        # Entry
        value = cleaned_values[idx] if idx < len(cleaned_values) else ""
        is_valid = validate_field(col, value)
        
        # Crear entry con estilo según validación
        if col == COLUMNA_DATOS_EXTRA:
            # Para datos extra, usar un campo de texto más grande
            entry = ttk.Entry(field_frame, width=50, bootstyle="warning")
        else:
            entry = ttk.Entry(field_frame, width=30, 
                             bootstyle="default" if is_valid else "danger")
        
        # Insertar valor (ya limpio de nan)
        entry.insert(0, value)
        entry.pack(side=LEFT, fill=X, expand=True)
        
        # Agregar validación en tiempo real solo para campos con patrón
        if col in patrones:
            entry.bind("<KeyRelease>", lambda e, c=col, ent=entry: update_field_color(c, ent))
        
        entries[col] = entry

    # Agregar checkbox para mantener datos extra (si existe esa columna)
    if COLUMNA_DATOS_EXTRA in tree["columns"]:
        checkbox_frame = ttk.Frame(edit_win)
        checkbox_frame.grid(row=len(tree["columns"]), column=0, columnspan=2, padx=5, pady=10, sticky="w")
        
        ttk.Checkbutton(
            checkbox_frame, 
            text="Mantener datos extra", 
            variable=mantener_datos_extra,
            bootstyle="warning"
        ).pack(side=LEFT)

    def save_row():
        new_values = [entries[c].get() for c in tree["columns"]]
        row = dict(zip(tree["columns"], new_values))

        # Validar todos los campos principales
        campos_invalidos = []
        todos_campos_validos = True
        
        for col, patron in patrones.items():
            if col in row and row[col] != "" and not validar(row[col], patron):
                campos_invalidos.append(f"{col}: {row[col]}")
                todos_campos_validos = False
        
        # Verificar si tiene datos extra
        tiene_datos_extra = False
        if COLUMNA_DATOS_EXTRA in row and row[COLUMNA_DATOS_EXTRA].strip() != "":
            tiene_datos_extra = True

        # Si hay campos inválidos
        if campos_invalidos:
            mensaje = "Los siguientes campos no son correctos:\n" + "\n".join(campos_invalidos)
            if tiene_datos_extra and not mantener_datos_extra.get():
                mensaje += "\n\nNota: Los datos extra no se guardarán a menos que marque la opción correspondiente."
            Messagebox.show_error(title="Error de validación", message=mensaje)
            return

        # Si todos los campos son válidos y el usuario quiere mantener datos extra
        if todos_campos_validos and tiene_datos_extra and mantener_datos_extra.get():
            # Mostrar advertencia
            respuesta = Messagebox.show_question(
                title="Confirmar datos extra",
                message="¿Está seguro de que desea guardar este registro con datos adicionales?\n\n" +
                        f"Datos extra: {row[COLUMNA_DATOS_EXTRA]}",
                buttons=["Sí:primary", "No:secondary"]
            )
            
            if respuesta == "No":
                return
            
            # Preparar para guardar con datos extra
            guardar_con_datos_extra = True
            row_para_guardar = row.copy()
        else:
            # Guardar sin datos extra (comportamiento normal)
            guardar_con_datos_extra = False
            row_para_guardar = {k: v for k, v in row.items() if k != COLUMNA_DATOS_EXTRA}
        
        # Manejar el archivo validos.csv
        if os.path.exists(FILE_VALIDOS):
            # Leer el archivo existente
            df_validos = pd.read_csv(FILE_VALIDOS)
            
            # Si vamos a guardar con datos extra y el CSV no tiene esa columna
            if guardar_con_datos_extra and COLUMNA_DATOS_EXTRA not in df_validos.columns:
                # Agregar la columna "Datos extra" vacía a todos los registros existentes
                df_validos[COLUMNA_DATOS_EXTRA] = ""
                # Reordenar columnas para que "Datos extra" esté al final
                cols = [col for col in df_validos.columns if col != COLUMNA_DATOS_EXTRA]
                cols.append(COLUMNA_DATOS_EXTRA)
                df_validos = df_validos[cols]
                # Guardar el DataFrame actualizado
                df_validos.to_csv(FILE_VALIDOS, index=False)
            
            # Si el CSV tiene la columna "Datos extra" pero no vamos a guardar con datos extra
            elif not guardar_con_datos_extra and COLUMNA_DATOS_EXTRA in df_validos.columns:
                # Agregar el campo vacío para mantener consistencia
                row_para_guardar[COLUMNA_DATOS_EXTRA] = ""
        
        # Guardar el nuevo registro
        file_exists = os.path.exists(FILE_VALIDOS)
        
        if file_exists:
            # Leer de nuevo para asegurar que tenemos la estructura correcta
            df_validos = pd.read_csv(FILE_VALIDOS)
            # Agregar el nuevo registro
            df_nuevo = pd.DataFrame([row_para_guardar])
            # Asegurar que las columnas coincidan
            for col in df_validos.columns:
                if col not in df_nuevo.columns:
                    df_nuevo[col] = ""
            # Reordenar columnas para que coincidan
            df_nuevo = df_nuevo[df_validos.columns]
            # Concatenar y guardar
            df_final = pd.concat([df_validos, df_nuevo], ignore_index=True)
            df_final.to_csv(FILE_VALIDOS, index=False)
        else:
            # Si el archivo no existe, crear uno nuevo
            pd.DataFrame([row_para_guardar]).to_csv(FILE_VALIDOS, index=False)

        # Eliminar de la tabla y actualizar archivo de inválidos
        tree.delete(item)
        update_invalidos_file()

        # Mensaje de confirmación
        if tiene_datos_extra and mantener_datos_extra.get() and todos_campos_validos:
            Messagebox.show_info(
                title="Correcto", 
                message="Fila guardada en validos.csv con datos adicionales.\n"
            )
        else:
            Messagebox.show_info(
                title="Correcto", 
                message="Fila corregida y guardada en validos.csv"
            )
        
        edit_win.destroy()

    def cancel_edit():
        edit_win.destroy()

    # Frame para botones
    btn_frame = ttk.Frame(edit_win)
    # Ajustar la posición según si hay checkbox o no
    row_position = len(tree["columns"]) + 1 if COLUMNA_DATOS_EXTRA in tree["columns"] else len(tree["columns"])
    btn_frame.grid(row=row_position, column=0, columnspan=2, pady=10)
    
    ttk.Button(btn_frame, text="Guardar cambios", bootstyle="success", 
               command=save_row).pack(side=LEFT, padx=5)
    ttk.Button(btn_frame, text="Cancelar", bootstyle="secondary", 
               command=cancel_edit).pack(side=LEFT, padx=5)
    
    # Centrar la ventana en la pantalla
    edit_win.update_idletasks()
    width = edit_win.winfo_width()
    height = edit_win.winfo_height()
    x = (edit_win.winfo_screenwidth() // 2) - (width // 2)
    y = (edit_win.winfo_screenheight() // 2) - (height // 2)
    edit_win.geometry(f'{width}x{height}+{x}+{y}')
    
    # Manejar el cierre con el protocolo de ventana
    edit_win.protocol("WM_DELETE_WINDOW", cancel_edit)

def edit_selected_rows():
    selection = tree.selection()
    if not selection:
        Messagebox.show_warning(title="Atención", message="Seleccione al menos una fila.")
        return
    for item in selection:
        edit_row(item)

def on_double_click(event):
    item = tree.identify_row(event.y)
    if item:
        edit_row(item)

tree.bind("<Double-1>", on_double_click)

# -------------------------------
# Botones
# -------------------------------
btn_frame = ttk.Frame(root)
btn_frame.pack(pady=10)

btn_edit = ttk.Button(btn_frame, text="Editar selección", bootstyle="primary", command=edit_selected_rows)
btn_edit.grid(row=0, column=0, padx=5)

# Añadir leyenda
legend_frame = ttk.Frame(root)
legend_frame.pack(side=TOP, pady=5)
ttk.Label(legend_frame, text="❌ = Campo con error | La columna 'Datos extra' contiene campos adicionales", bootstyle="info").pack()

# -------------------------------
# Cargar datos iniciales
# -------------------------------
if os.path.exists(FILE_INVALIDOS):
    try:
        if os.path.getsize(FILE_INVALIDOS) == 0:
            df = pd.DataFrame(columns=COLUMNAS_PRINCIPALES)
            update_status("El archivo inválidos.csv está vacío. No hay registros pendientes.")
            cargar_tabla(df)
        else:
            df = leer_csv_flexible(FILE_INVALIDOS)
            
            # Si el DataFrame no está vacío, procesarlo
            if not df.empty:
                # Aplicar el procesamiento
                df = procesar_datos_extra(df)
                
                cargar_tabla(df)
                
                # Actualizar estado
                num_filas = len(df)
                if COLUMNA_DATOS_EXTRA in df.columns:
                    filas_con_extras = df[df[COLUMNA_DATOS_EXTRA].str.strip() != ""].shape[0]
                    if filas_con_extras > 0:
                        update_status(f"{num_filas} filas inválidas cargadas ({filas_con_extras} con datos adicionales)")
                    else:
                        update_status(f"{num_filas} filas inválidas cargadas")
                else:
                    update_status(f"{num_filas} filas inválidas cargadas")
            else:
                df = pd.DataFrame(columns=COLUMNAS_PRINCIPALES)
                update_status("El archivo inválidos.csv no contiene registros.")
                cargar_tabla(df)
                
    except Exception as e:
        df = pd.DataFrame(columns=COLUMNAS_PRINCIPALES)
        update_status(f"Error al cargar el archivo: {str(e)}")
        print(f"Error detallado: {e}")
        import traceback
        traceback.print_exc()
        cargar_tabla(df)
else:
    df = pd.DataFrame(columns=COLUMNAS_PRINCIPALES)
    update_status("No se encontró archivo de inválidos.")
    cargar_tabla(df)

root.mainloop()