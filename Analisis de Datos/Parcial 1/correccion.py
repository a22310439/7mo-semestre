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

def validar(valor, patron):
    """Valida un campo contra un patrón regex"""
    return bool(re.match(patron, str(valor).strip())) if pd.notna(valor) else False

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
        max_len = max([len(str(val)) for val in df[col].values] + [len(col)]) * 10
        tree.column(col, width=max_len, anchor="center")

    # Insertar filas con indicación de campos erróneos
    for _, row in df.iterrows():
        values = []
        for col in df.columns:
            val = row[col]
            # Si el campo es inválido, agregar un indicador visual
            if col in patrones and not validar(val, patrones[col]):
                values.append(f"❌ {val}")
            else:
                values.append(val)
        
        tree.insert("", "end", values=values)

def update_invalidos_file():
    """Guarda el estado actual del Treeview en invalidos.csv"""
    invalid_rows = []
    for item in tree.get_children():
        values = tree.item(item)["values"]
        # Limpiar los indicadores ❌ antes de guardar
        cleaned_values = []
        for val in values:
            if isinstance(val, str) and val.startswith("❌ "):
                cleaned_values.append(val[2:])  # Remover "❌ "
            else:
                cleaned_values.append(val)
        
        invalid_rows.append(dict(zip(tree["columns"], cleaned_values)))

    if invalid_rows:
        pd.DataFrame(invalid_rows).to_csv(FILE_INVALIDOS, index=False)
    else:
        open(FILE_INVALIDOS, "w").write("")

def edit_row(item):
    """Abre ventana para editar una fila"""
    old_values = tree.item(item)["values"]
    
    # Limpiar valores de indicadores ❌
    cleaned_values = []
    for val in old_values:
        if isinstance(val, str) and val.startswith("❌ "):
            cleaned_values.append(val[2:])
        else:
            cleaned_values.append(val)
    
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
        entry = ttk.Entry(field_frame, width=30, 
                         bootstyle="default" if is_valid else "danger")
        entry.insert(0, value)
        entry.pack(side=LEFT, fill=X, expand=True)
        
        # Agregar validación en tiempo real
        if col in patrones:
            entry.bind("<KeyRelease>", lambda e, c=col, ent=entry: update_field_color(c, ent))
        
        entries[col] = entry

    def save_row():
        new_values = [entries[c].get() for c in tree["columns"]]
        row = dict(zip(tree["columns"], new_values))

        # Validar todos los campos antes de guardar
        campos_invalidos = []
        for col, patron in patrones.items():
            if not validar(row[col], patron):
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
ttk.Label(legend_frame, text="❌ = Campo con error", bootstyle="info").pack()

# -------------------------------
# Cargar datos iniciales
# -------------------------------
if os.path.exists(FILE_INVALIDOS):
    try:
        if os.path.getsize(FILE_INVALIDOS) == 0:
            df = pd.DataFrame(columns=list(patrones.keys()))
            update_status("El archivo inválidos.csv está vacío. No hay registros pendientes.")
        else:
            df = pd.read_csv(FILE_INVALIDOS)
            if df.empty:
                df = pd.DataFrame(columns=list(patrones.keys()))
                update_status("El archivo inválidos.csv no contiene registros.")
            else:
                cargar_tabla(df)
                update_status(f"{len(df)} filas inválidas cargadas")
    except EmptyDataError:
        df = pd.DataFrame(columns=list(patrones.keys()))
        update_status("El archivo inválidos.csv está vacío. No hay registros pendientes.")
else:
    df = pd.DataFrame(columns=list(patrones.keys()))
    update_status("No se encontró archivo de inválidos.")

root.mainloop()