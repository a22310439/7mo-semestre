import csv
import random

nom_masculinos = ['Juan', 'José', 'Carlos', 'Santiago', 'Darío', 'Luis', 'Omar', 'Oscar', 'Germán', 'Antonio', 'Gerardo', 'Manuel', 'Armando', 'Daniel', 'Miguel', 'Pedro']
nom_femeninos = ['Ana', 'María', 'Cristina', 'Carla', 'Daniela', 'Andrea', 'Denise', 'Brenda', 'Alma', 'Rebeca', 'Isabel', 'Lucia', 'Carmen', 'Itzel', 'Casandra']
apellidosLista = ['García', 'López', 'Macías', 'Maciel', 'Carrillo', 'Pérez', 'Aréchiga', 'Torres', 'Córdova', 'Cuevas', 'Hernández', 'Miramontes']
dominios = ['gmail.com', 'hotmail.com', 'yahoo.com', 'outlook.com']

# Porcentaje de registros con ruido
porcentaje_ruido = 0.1

with open('personas.csv', 'w', newline='', encoding='utf-8') as archivo:
    escritor = csv.writer(archivo)
    escritor.writerow(['Nombre', 'Apellidos', 'Email', 'Telefono', 'Sexo', 'Edad'])

    for i in range(100):
        sexo = random.choice(['M', 'F'])
        nombre = random.choice(nom_masculinos if sexo == 'M' else nom_femeninos)
        apellidoPaterno = random.choice(apellidosLista)
        apellidoMaterno = random.choice(apellidosLista)
        apellidos = f"{apellidoPaterno} {apellidoMaterno}"
        email = f"{nombre.lower()}.{apellidoPaterno.lower()}{random.randint(1,99)}@{random.choice(dominios)}"
        telefono = f"{random.randint(3300000000, 3399999999)}"
        edad = random.randint(1, 99)

        # Decidir si este registro tendrá ruido
        if random.random() < porcentaje_ruido:
            error_tipo = random.choice(['nombre', 'apellido', 'email', 'telefono', 'sexo', 'edad'])
            
            if error_tipo == 'nombre':
                nombre += random.choice(['XX', '*error*', '123'])
            elif error_tipo == 'apellido':
                apellidos = apellidoPaterno + random.choice(['123', '_inv', '**']) + " " + apellidoMaterno
            elif error_tipo == 'email':
                email = email.replace('@', random.choice(['(*2@', '[error]@', ' @']))
            elif error_tipo == 'telefono':
                telefono += random.choice(['-999', 'abc', '***'])
            elif error_tipo == 'sexo':
                sexo += random.choice(['X', '_inv', '??'])
            elif error_tipo == 'edad':
                edad = str(edad) + random.choice(['a', '??', '.5'])

        escritor.writerow([nombre, apellidos, email, telefono, sexo, edad])

print("CSV generado.")
