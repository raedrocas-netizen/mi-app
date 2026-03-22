from flask import Flask, render_template, request, redirect, session, send_file
import psycopg2
import os
from werkzeug.security import generate_password_hash, check_password_hash
from reportlab.platypus import SimpleDocTemplate, Table

app = Flask(__name__)
app.secret_key = "clave_secreta"


# 🔌 CONEXIÓN A POSTGRES
def get_connection():
    return psycopg2.connect(os.environ.get("DATABASE_URL"))


# 🗄️ CREAR TABLAS
def crear_bd():
    con = get_connection()
    cur = con.cursor()

    cur.execute("""
    CREATE TABLE IF NOT EXISTS usuarios(
        id SERIAL PRIMARY KEY,
        username TEXT,
        password TEXT
    )
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS pedidos(
        id SERIAL PRIMARY KEY,
        codigo TEXT,
        producto TEXT,
        cliente TEXT,
        cantidad INTEGER,
        precio NUMERIC
    )
    """)

    con.commit()
    con.close()


crear_bd()


# 🔐 LOGIN
@app.route("/", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        user = request.form["username"]
        pwd = request.form["password"]

        con = get_connection()
        cur = con.cursor()
        cur.execute("SELECT * FROM usuarios WHERE username=%s", (user,))
        usuario = cur.fetchone()
        con.close()

        if usuario and check_password_hash(usuario[2], pwd):
            session["user"] = user
            return redirect("/inicio")

    return render_template("login.html")


# 🧾 REGISTRO
@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        user = request.form["username"]
        pwd = generate_password_hash(request.form["password"])

        con = get_connection()
        cur = con.cursor()
        cur.execute(
            "INSERT INTO usuarios (username, password) VALUES (%s, %s)",
            (user, pwd)
        )
        con.commit()
        con.close()

        return redirect("/")

    return render_template("register.html")


# 🔓 LOGOUT
@app.route("/logout")
def logout():
    session.clear()
    return redirect("/")


# 🏠 INICIO
@app.route("/inicio")
def inicio():
    if "user" not in session:
        return redirect("/")
    return render_template("index.html")


# ➕ AGREGAR
@app.route("/agregar", methods=["POST"])
def agregar():
    datos = (
        request.form["codigo"],
        request.form["producto"],
        request.form["cliente"],
        request.form["cantidad"],
        request.form["precio"]
    )

    con = get_connection()
    cur = con.cursor()
    cur.execute(
        "INSERT INTO pedidos (codigo, producto, cliente, cantidad, precio) VALUES (%s, %s, %s, %s, %s)",
        datos
    )
    con.commit()
    con.close()

    return redirect("/lista")


# 📋 LISTA
@app.route("/lista")
def lista():
    if "user" not in session:
        return redirect("/")

    buscar = request.args.get("buscar", "")

    con = get_connection()
    cur = con.cursor()

    if buscar:
        cur.execute(
            "SELECT * FROM pedidos WHERE cliente ILIKE %s OR codigo ILIKE %s",
            ('%' + buscar + '%', '%' + buscar + '%')
        )
    else:
        cur.execute("SELECT * FROM pedidos")

    pedidos_raw = cur.fetchall()

    pedidos = []
    total_general = 0

    for p in pedidos_raw:
        subtotal = p[4] * p[5]  # cantidad * precio
        total_general += subtotal

        pedidos.append(p + (subtotal,))
    con.close()
    return render_template("lista.html", pedidos=pedidos, total=total_general)


# ❌ ELIMINAR
@app.route("/eliminar/<int:id>")
def eliminar(id):
    con = get_connection()
    cur = con.cursor()
    cur.execute("DELETE FROM pedidos WHERE id=%s", (id,))
    con.commit()
    con.close()

    return redirect("/lista")


# ✏️ EDITAR
@app.route("/editar/<int:id>", methods=["GET", "POST"])
def editar(id):
    con = get_connection()
    cur = con.cursor()

    if request.method == "POST":
        datos = (
            request.form["codigo"],
            request.form["producto"],
            request.form["cliente"],
            request.form["cantidad"],
            request.form["precio"],
            id
        )

        cur.execute(
            "UPDATE pedidos SET codigo=%s, producto=%s, cliente=%s, cantidad=%s, precio=%s WHERE id=%s",
            datos
        )
        con.commit()
        con.close()

        return redirect("/lista")

    cur.execute("SELECT * FROM pedidos WHERE id=%s", (id,))
    p = cur.fetchone()
    con.close()

    return render_template("editar.html", p=p)


# 📄 PDF
@app.route("/pdf")
def pdf():
    con = get_connection()
    cur = con.cursor()
    cur.execute("SELECT codigo, producto, cliente, cantidad, precio FROM pedidos")
    datos = cur.fetchall()
    con.close()

    archivo = "pedidos.pdf"
    doc = SimpleDocTemplate(archivo)
    tabla = Table([["Código", "Producto", "Cliente", "Cantidad"]] + datos)
    doc.build([tabla])

    return send_file(archivo, as_attachment=True)


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)