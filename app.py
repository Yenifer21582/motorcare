from flask import Flask, render_template, request, redirect, session
from functools import wraps
from flask import make_response
import mysql.connector
import os

app = Flask(__name__)
app.secret_key = "motorcare123"
# ===========================
# PROTEGER RUTAS
# ===========================

def login_requerido(f):

    @wraps(f)
    def decorador(*args, **kwargs):

        if "nombre" not in session:
            return redirect("/?mensaje=Debe iniciar sesión")

        return f(*args, **kwargs)

    return decorador


conexion = mysql.connector.connect(
    host=os.environ.get("DB_HOST", "localhost"),
    user=os.environ.get("DB_USER", "root"),
    password=os.environ.get("DB_PASSWORD", ""),
    database=os.environ.get("DB_NAME", "motorcare"),
    port=int(os.environ.get("DB_PORT", 3306))
)

# ===========================
# INICIO DE SESIÓN
# ===========================

@app.route("/")
def login():

    mensaje = request.args.get("mensaje")
    return render_template("index.html", mensaje=mensaje)

@app.route("/", methods=["POST"])
def iniciar_sesion():

    correo = request.form["correo"]
    contrasena = request.form["contrasena"]
    rol = request.form["rol"]

    cursor = conexion.cursor(dictionary=True)

    sql = "SELECT * FROM usuarios WHERE correo=%s AND contrasena=%s"
    valores = (correo, contrasena)

    cursor.execute(sql, valores)

    usuario = cursor.fetchone()

    if usuario:

        if usuario["rol"] == rol:

            session["nombre"] = usuario["nombre"]
            session["rol"] = usuario["rol"]

            if usuario["rol"] == "cliente":
                return render_template(
                    "dashboard.html",
                    nombre=usuario["nombre"],
                    login_exitoso=True
                )

            elif usuario["rol"] == "admin":

                # Contar usuarios registrados
                cursor.execute("SELECT COUNT(*) AS total FROM usuarios")
                total_usuarios = cursor.fetchone()["total"]

                # Contar citas registradas
                cursor.execute("SELECT COUNT(*) AS total FROM citas")
                total_citas = cursor.fetchone()["total"]

                return render_template(
                    "dashboard_admin.html",
                    nombre=usuario["nombre"],
                    login_admin=True,
                    total_usuarios=total_usuarios,
                    total_citas=total_citas
                )

    return redirect("/?login=error")
# ===========================
# REGISTRO
# ===========================

@app.route("/registro")
def pagina_registro():
    return render_template("registro.html")


@app.route("/registro", methods=["POST"])
def registrar():

    nombre = request.form["nombre"]
    correo = request.form["correo"]
    contrasena = request.form["contrasena"]
    rol = "cliente"
    cursor = conexion.cursor()

    sql = "INSERT INTO usuarios (nombre, correo, contrasena , rol) VALUES (%s, %s, %s , %s)"
    valores = (nombre, correo, contrasena, rol)

    cursor.execute(sql, valores)
    conexion.commit()

    cursor.close()

    return redirect("/?registro=ok")


# ===========================
# OLVIDAR CONTRASEÑA
# ===========================

@app.route("/olvidar")
def olvidar():
    return render_template("olvidar.html")

@app.route("/olvidar", methods=["POST"])
def cambiar_contrasena():

    correo = request.form["correo"]
    nueva_contrasena = request.form["nueva_contrasena"]
    confirmar_contrasena = request.form["confirmar_contrasena"]

    if nueva_contrasena != confirmar_contrasena:
        return "Las contraseñas no coinciden."

    cursor = conexion.cursor()

    sql = "UPDATE usuarios SET contrasena=%s WHERE correo=%s"
    valores = (nueva_contrasena, correo)

    cursor.execute(sql, valores)
    conexion.commit()

    if cursor.rowcount == 0:
        cursor.close()
        return "El correo no está registrado."

    cursor.close()

    return redirect("/?mensaje=contrasena_actualizada")

@app.route("/configuracion")
def configuracion():
    return render_template("configuracion.html")

    # ===========================
# SERVICIOS
# ===========================

@app.route("/servicios")
@login_requerido
def servicios():
    return render_template(
        "servicios.html",
        nombre=session.get("nombre")
    )

@app.route("/tipos-servicio")
@login_requerido
def tipos_servicio():
    return render_template(
        "tipos_servicio.html",
        nombre=session.get("nombre")
    )

@app.route("/agenda", methods=["GET", "POST"])
@login_requerido
def agenda():

    if request.method == "POST":

        nombre = request.form["nombre"]
        correo = request.form["correo"]
        telefono = request.form["telefono"]
        vehiculo = request.form["vehiculo"]
        servicio = request.form["servicio"]
        fecha = request.form["fecha"]
        hora = request.form["hora"]

        cursor = conexion.cursor()

        sql = """
        INSERT INTO citas
        (nombre, correo, telefono, vehiculo, servicio, fecha, hora)
        VALUES (%s,%s,%s,%s,%s,%s,%s)
        """

        valores = (
            nombre,
            correo,
            telefono,
            vehiculo,
            servicio,
            fecha,
            hora
        )

        cursor.execute(sql, valores)
        conexion.commit()
        cursor.close()

        return render_template(
    "agenda.html",
    cita_guardada=True,
    vehiculo=vehiculo,
    servicio=servicio,
    fecha=fecha,
    hora=hora
)

    return render_template(
    "agenda.html",
    nombre=session.get("nombre")
)

@app.route("/consejos")
@login_requerido
def consejos():
    return render_template(
        "consejos.html",
        nombre=session.get("nombre")
    )

@app.route("/usuarios")
@login_requerido
def usuarios():

    mensaje = request.args.get("mensaje")

    cursor = conexion.cursor(dictionary=True)

    cursor.execute("SELECT * FROM usuarios")
    lista_usuarios = cursor.fetchall()

    cursor.execute("SELECT COUNT(*) AS total FROM usuarios")
    total_usuarios = cursor.fetchone()["total"]

    cursor.execute("SELECT COUNT(*) AS total FROM usuarios WHERE rol='cliente'")
    total_clientes = cursor.fetchone()["total"]

    cursor.execute("SELECT COUNT(*) AS total FROM usuarios WHERE rol='admin'")
    total_admin = cursor.fetchone()["total"]

    cursor.close()

    return render_template(
    "usuarios.html",
    usuarios=lista_usuarios,
    total_usuarios=total_usuarios,
    total_clientes=total_clientes,
    total_admin=total_admin,
    mensaje=mensaje
)

@app.route("/editar_usuario/<int:id>", methods=["GET", "POST"])
def editar_usuario(id):

    cursor = conexion.cursor(dictionary=True)

    if request.method == "POST":

        nombre = request.form["nombre"]
        correo = request.form["correo"]
        rol = request.form["rol"]

        cursor.execute("""
            UPDATE usuarios
            SET nombre=%s,
                correo=%s,
                rol=%s
            WHERE id=%s
        """, (nombre, correo, rol, id))

        conexion.commit()

        cursor.close()

        return redirect("/usuarios?mensaje=editado")

    cursor.execute("SELECT * FROM usuarios WHERE id=%s", (id,))
    usuario = cursor.fetchone()

    cursor.close()

    return render_template(
        "editar_usuario.html",
        usuario=usuario
    )
# ===========================
# DASHBOARD
# ===========================

@app.route("/cerrar")
def cerrar():

    session.clear()

    return redirect("/?mensaje=logout")

@app.route("/dashboard")
@login_requerido
def dashboard():
    return render_template(
        "dashboard.html",
        nombre=session.get("nombre")
    )

@app.route("/dashboard_admin")
@login_requerido
def dashboard_admin():

    cursor = conexion.cursor(dictionary=True)

    cursor.execute("SELECT COUNT(*) AS total FROM usuarios")
    total_usuarios = cursor.fetchone()["total"]

    cursor.execute("SELECT COUNT(*) AS total FROM citas")
    total_citas = cursor.fetchone()["total"]

    cursor.close()

    return render_template(
    "dashboard_admin.html",
    nombre=session.get("nombre"),
    total_usuarios=total_usuarios,
    total_citas=total_citas
)


    # ===========================
# CITAS
# ===========================

@app.route("/citas")
@login_requerido
def citas():

    cursor = conexion.cursor(dictionary=True)

    cursor.execute("SELECT * FROM citas")
    lista_citas = cursor.fetchall()

    cursor.close()

    return render_template(
        "citas.html",
        citas=lista_citas
    )

@app.route("/servicios_admin")
@login_requerido
def servicios_admin():

    cursor = conexion.cursor(dictionary=True)

    cursor.execute("""
        SELECT
            servicio,
            GROUP_CONCAT(nombre SEPARATOR ', ') AS clientes,
            COUNT(*) AS cantidad
        FROM citas
        GROUP BY servicio
        ORDER BY cantidad DESC
    """)

    datos = cursor.fetchall()

    cursor.execute("SELECT COUNT(*) AS total FROM citas")
    total_servicios = cursor.fetchone()["total"]

    cursor.execute("""
        SELECT servicio, COUNT(*) AS cantidad
        FROM citas
        GROUP BY servicio
        ORDER BY cantidad DESC
        LIMIT 1
    """)

    mas_solicitado = cursor.fetchone()

    cursor.close()

    return render_template(
        "servicios_admin.html",
        datos=datos,
        total_servicios=total_servicios,
        mas_solicitado=mas_solicitado
    )
# ===========================
# CONFIGURACIÓN ADMIN
# ===========================

@app.route("/configuracion_admin")
@login_requerido
def configuracion_admin():
    return render_template("configuracion_admin.html")


# ===========================
# EJECUTAR FLASK
# ===========================

@app.after_request
def add_header(response):
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Pragma"] = "no-cache"
    response.headers["Expires"] = "0"
    return response


if __name__ == "__main__":
    app.run(debug=True) 