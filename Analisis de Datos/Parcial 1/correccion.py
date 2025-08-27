import ttkbootstrap as ttk
from ttkbootstrap.constants import *
from ttkbootstrap.dialogs import Messagebox
import pandas as pd
import re
import os

# Cargar registros inválidos
df = pd.read_csv("invalidos.csv")

# Patrones de validación
patrones = {
    "Nombre": r"^[A-Z][a-zÀ-ÿ\u00f1\u00d1]*(\s[A-Z][a-zÀ-ÿ\u00f1\u00d1]*)?$",
    "Apellidos": r"^[A-Z][a-zÀ-ÿ\u00f1\u00d1]*(\s[A-Z][a-zÀ-ÿ\u00f1\u00d1]*)?$",
    "Email": r"^[\w\.]+@[\w\.]+\.\w+$",
    "Telefono": r"^\d{10}$",
    "Sexo": r"^(M|F)$",
    "Edad": r"^\d{1,3}$"
}

def validar(valor, patron):
    return bool(re.match(patron, str(valor).strip())) if pd.notna(valor) else False

# --- UI ---
root = ttk.Window(themename="darkly")
root.title("Editor de Registros Inválidos")
root.geometry("800x500")

# Marco de tabla con barra de desplazamiento
frame = ttk.Frame(root)
frame.pack(fill=BOTH, expand=True, padx=10, pady=10)

tree = ttk.Treeview(frame, columns=list(df.columns), show="headings", bootstyle="info") 
tree.pack(side=LEFT, fill=BOTH, expand=True)

scroll = ttk.Scrollbar(frame, command=tree.yview, orient="vertical")
scroll.pack(side=RIGHT, fill=Y)
tree.configure(yscrollcommand=scroll.set)

# Encabezados de tabla
for col in df.columns:
    tree.heading(col, text=col)
    tree.column(col, width=120, anchor="center")

for _, row in df.iterrows():
    tree.insert("", "end", values=list(row))

# --- Lógica de edición y validación ---

def edit_row(item):
    old_values = tree.item(item)["values"]
    edit_win = ttk.Toplevel(root)
    edit_win.title("Editar fila")
    entries = {}

    for idx, col in enumerate(df.columns):
        ttk.Label(edit_win, text=col).grid(row=idx, column=0, padx=5, pady=5, sticky="w")
        entry = ttk.Entry(edit_win, width=30)
        entry.insert(0, old_values[idx])
        entry.grid(row=idx, column=1, padx=5, pady=5)
        entries[col] = entry

    def save_row():
        new_values = [entries[c].get() for c in df.columns]
        row = dict(zip(df.columns, new_values))

        # Validar todos los campos antes de guardar
        campos_invalidos = []
        for col, patron in patrones.items():
            if not validar(row[col], patron):
                campos_invalidos.append(f"{col}: {row[col]}")
        
        # Si hay campos inválidos, mostrar error
        if campos_invalidos:
            mensaje = "Los siguientes campos no son correctos:\n" + "\n".join(campos_invalidos)
            Messagebox.show_error(title="Error de validación", message=mensaje)
            return
        
        # Si todo es válido, guardar y cerrar
        file_exists = os.path.exists("validos.csv")
        pd.DataFrame([row]).to_csv(
            "validos.csv", index=False, mode="a", header=not file_exists
        )

        tree.delete(item)
        update_invalidos_file()

        Messagebox.show_info(title="Correcto", message="Fila corregida y guardada en validos.csv")
        edit_win.destroy()

    ttk.Button(edit_win, text="Guardar cambios", bootstyle="success", command=save_row)\
        .grid(row=len(df.columns), column=0, columnspan=2, pady=10)

def update_invalidos_file():
    invalid_rows = []
    for item in tree.get_children():
        values = tree.item(item)["values"]
        invalid_rows.append(dict(zip(df.columns, values)))

    if invalid_rows:
        pd.DataFrame(invalid_rows).to_csv("invalidos.csv", index=False)
    else:
        open("invalidos.csv", "w").write("")

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

# Boton
btn_frame = ttk.Frame(root)
btn_frame.pack(pady=10)

ttk.Button(btn_frame, text="Editar selección", bootstyle="primary", command=edit_selected_rows)\
    .grid(row=0, column=0, padx=5)


root.mainloop()