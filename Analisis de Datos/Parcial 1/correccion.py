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

# Columnas esperadas (las 6 principales)
COLUMNAS_PRINCIPALES = ["Nombre", "Apellidos", "Email", "Telefono", "Sexo", "Edad"]
COLUMNA_DATOS_EXTRA = "Datos extra"

def validar(valor, patron):
    """Valida un campo contra un patrón regex"""
    return bool(re.match(patron, str(valor).strip())) if pd.notna(valor) else False

def procesar_datos_extra(df):
    """Procesa el DataFrame para manejar columnas adicionales"""
    # Asegurarse de que el DataFrame no esté vacío
    if df.empty:
        return df
    
    # Obtener todas las columnas del DataFrame
    todas_columnas = list(df.columns)
    
    # Limpiar nombres de columnas (quitar espacios extras)
    df.columns = df.columns.str.strip()
    todas_columnas = list(df.columns)
    
    print(f"Procesando columnas: {todas_columnas}")  # Debug
    
    # Identificar columnas principales presentes
    columnas_principales_presentes = [col for col in COLUMNAS_PRINCIPALES if col in todas_columnas]
    
    # Si la columna "Datos extra" ya existe
    if COLUMNA_DATOS_EXTRA in todas_columnas:
        # Asegurarse de que no tenga valores NaN
        df[COLUMNA_DATOS_EXTRA] = df[COLUMNA_DATOS_EXTRA].fillna("")
        df[COLUMNA_DATOS_EXTRA] = df[COLUMNA_DATOS_EXTRA].astype(str)
        df[COLUMNA_DATOS_EXTRA] = df[COLUMNA_DATOS_EXTRA].replace("nan", "")
        
        # Si todos los valores están vacíos, eliminar la columna
        if df[COLUMNA_DATOS_EXTRA].str.strip().eq("").all():
            df = df.drop(columns=[COLUMNA_DATOS_EXTRA])
            columnas_finales = columnas_principales_presentes
        else:
            columnas_finales = columnas_principales_presentes + [COLUMNA_DATOS_EXTRA]
    else:
        # Identificar columnas extras (que no son las principales)
        columnas_extras = [col for col in todas_columnas if col not in COLUMNAS_PRINCIPALES]
        
        if columnas_extras:
            # Crear nueva columna con los datos concatenados
            datos_extra_series = df[columnas_extras].apply(
                lambda row: ' | '.join([f"{col}: {row[col]}" for col in columnas_extras 
                                       if pd.notna(row[col]) and str(row[col]).strip() != ""]), 
                axis=1
            )
            
            # Solo agregar la columna si tiene algún dato
            if not datos_extra_series.str.strip().eq("").all():
                df[COLUMNA_DATOS_EXTRA] = datos_extra_series
                columnas_finales = columnas_principales_presentes + [COLUMNA_DATOS_EXTRA]
            else:
                columnas_finales = columnas_principales_presentes
            
            # Eliminar las columnas extras originales
            df = df.drop(columns=columnas_extras)
        else:
            columnas_finales = columnas_principales_presentes
    
    # Limpiar NaN en todas las columnas
    for col in df.columns:
        df[col] = df[col].fillna("")
        if df[col].dtype == 'object':
            df[col] = df[col].astype(str).replace("nan", "")
    
    # Reordenar y seleccionar solo las columnas finales
    df = df[columnas_finales]
    
    print(f"DataFrame procesado: {df.shape}")  # Debug
    print(f"Columnas finales: {list(df.columns)}")  # Debug
    
    return df

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

    for idx, col in enumerate(tree["columns"]):
        # Frame para cada campo
        field_frame = ttk.Frame(edit_win)
        field_frame.grid(row=idx, column=0, columnspan=2, padx=5, pady=5, sticky="ew")
        entry_frames[col] = field_frame
        
        # Label
        ttk.Label(field_frame, text=col, width=15).pack(side=LEFT, padx=(0, 5))
        
        # Entry
        value = cleaned_values[idx]
        is_valid = validate_field(col, value)
        
        # Crear entry con estilo según validación
        if col == COLUMNA_DATOS_EXTRA:
            # Para datos extra, usar un campo de texto más grande
            entry = ttk.Entry(field_frame, width=50, bootstyle="info")
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

    def save_row():
        new_values = [entries[c].get() for c in tree["columns"]]
        row = dict(zip(tree["columns"], new_values))

        # Validar todos los campos principales antes de guardar
        campos_invalidos = []
        for col, patron in patrones.items():
            if col in row and row[col] != "" and not validar(row[col], patron):
                campos_invalidos.append(f"{col}: {row[col]}")

        if campos_invalidos:
            mensaje = "Los siguientes campos no son correctos:\n" + "\n".join(campos_invalidos)
            Messagebox.show_error(title="Error de validación", message=mensaje)
            return

        # Guardar en validos.csv
        file_exists = os.path.exists(FILE_VALIDOS)
        pd.DataFrame([row]).to_csv(
            FILE_VALIDOS, index=False, mode="a", header=not file_exists
        )

        tree.delete(item)
        update_invalidos_file()

        Messagebox.show_info(title="Correcto", message="Fila corregida y guardada en validos.csv")
        edit_win.destroy()

    def cancel_edit():
        edit_win.destroy()

    # Frame para botones
    btn_frame = ttk.Frame(edit_win)
    btn_frame.grid(row=len(tree["columns"]), column=0, columnspan=2, pady=10)
    
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
            cargar_tabla(df)  # Cargar tabla vacía
        else:
            # Intentar leer el CSV con diferentes configuraciones
            try:
                # Primero intentar leer normalmente
                df = pd.read_csv(FILE_INVALIDOS)
            except:
                # Si falla, intentar con quote char
                try:
                    df = pd.read_csv(FILE_INVALIDOS, quotechar='"', quoting=1)
                except:
                    # Si aún falla, leer línea por línea
                    df = pd.read_csv(FILE_INVALIDOS, error_bad_lines=False)
            
            # Debug: imprimir información del DataFrame
            print(f"Columnas encontradas: {list(df.columns)}")
            print(f"Número de filas: {len(df)}")
            print(f"Primeras filas:\n{df.head()}")
            
            # Procesar datos extra si es necesario
            df = procesar_datos_extra(df)
            
            if df.empty:
                df = pd.DataFrame(columns=COLUMNAS_PRINCIPALES)
                update_status("El archivo inválidos.csv no contiene registros.")
                cargar_tabla(df)  # Cargar tabla vacía
            else:
                cargar_tabla(df)
                # Mostrar estado con información sobre datos extra
                num_filas = len(df)
                tiene_datos_extra = COLUMNA_DATOS_EXTRA in df.columns
                msg = f"{num_filas} filas inválidas cargadas"
                if tiene_datos_extra:
                    # Contar cuántas filas tienen datos extra
                    filas_con_extras = df[df[COLUMNA_DATOS_EXTRA].str.strip() != ""].shape[0] if tiene_datos_extra else 0
                    if filas_con_extras > 0:
                        msg += f" ({filas_con_extras} con datos adicionales)"
                update_status(msg)
    except EmptyDataError:
        df = pd.DataFrame(columns=COLUMNAS_PRINCIPALES)
        update_status("El archivo inválidos.csv está vacío. No hay registros pendientes.")
        cargar_tabla(df)  # Cargar tabla vacía
    except Exception as e:
        df = pd.DataFrame(columns=COLUMNAS_PRINCIPALES)
        update_status(f"Error al cargar el archivo: {str(e)}")
        print(f"Error detallado: {e}")  # Para debugging
        import traceback
        traceback.print_exc()  # Imprimir stack trace completo
        cargar_tabla(df)  # Cargar tabla vacía
else:
    df = pd.DataFrame(columns=COLUMNAS_PRINCIPALES)
    update_status("No se encontró archivo de inválidos.")
    cargar_tabla(df)  # Cargar tabla vacía

root.mainloop()