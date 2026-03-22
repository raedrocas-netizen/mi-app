from flask import Flask, render_template, request, redirect, session, send_file
import sqlite3
from werkzeug.security import generate_password_hash, check_password_hash
from reportlab.platypus import SimpleDocTemplate, Table

app = Flask(__name__)
app.secret_key = "clave_secreta"

# BD
def crear_bd():
    con = sqlite3.connect("database.db")
    cur = con.cursor()

    cur.execute("""
    CREATE TABLE IF NOT EXISTS usuarios(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT,
        password TEXT
    )
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS pedidos(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        codigo TEXT,
        producto TEXT,
        cliente TEXT,
        cantidad INTEGER
    )
    """)

    con.commit()
    con.close()

crear_bd()

# LOGIN
@app.route("/", methods=["GET","POST"])
def login():
    if request.method == "POST":
        user = request.form["username"]
        pwd = request.form["password"]

        con = sqlite3.connect("database.db")
        cur = con.cursor()
        cur.execute("SELECT * FROM usuarios WHERE username=?", (user,))
        usuario = cur.fetchone()
        con.close()

        if usuario and check_password_hash(usuario[2], pwd):
            session["user"] = user
            return redirect("/inicio")

    return render_template("login.html")

# REGISTRO
@app.route("/register", methods=["GET","POST"])
def register():
    if request.method == "POST":
        user = request.form["username"]
        pwd = generate_password_hash(request.form["password"])

        con = sqlite3.connect("database.db")
        cur = con.cursor()
        cur.execute("INSERT INTO usuarios (username,password) VALUES (?,?)", (user,pwd))
        con.commit()
        con.close()

        return redirect("/")

    return render_template("register.html")

# LOGOUT
@app.route("/logout")
def logout():
    session.clear()
    return redirect("/")

# INICIO APP
@app.route("/inicio")
def inicio():
    if "user" not in session:
        return redirect("/")
    return render_template("index.html")

# AGREGAR
@app.route("/agregar", methods=["POST"])
def agregar():
    datos = (
        request.form["codigo"],
        request.form["producto"],
        request.form["cliente"],
        request.form["cantidad"]
    )

    con = sqlite3.connect("database.db")
    cur = con.cursor()
    cur.execute("INSERT INTO pedidos (codigo,producto,cliente,cantidad) VALUES (?,?,?,?)", datos)
    con.commit()
    con.close()

    return redirect("/lista")

# LISTA
@app.route("/lista")
def lista():
    if "user" not in session:
        return redirect("/")

    buscar = request.args.get("buscar","")

    con = sqlite3.connect("database.db")
    cur = con.cursor()

    if buscar:
        cur.execute("SELECT * FROM pedidos WHERE cliente LIKE ? OR codigo LIKE ?",('%'+buscar+'%','%'+buscar+'%'))
    else:
        cur.execute("SELECT * FROM pedidos")

    pedidos = cur.fetchall()

    cur.execute("SELECT SUM(cantidad) FROM pedidos")
    total = cur.fetchone()[0]

    con.close()

    return render_template("lista.html", pedidos=pedidos, total=total)

# ELIMINAR
@app.route("/eliminar/<int:id>")
def eliminar(id):
    con = sqlite3.connect("database.db")
    cur = con.cursor()
    cur.execute("DELETE FROM pedidos WHERE id=?", (id,))
    con.commit()
    con.close()
    return redirect("/lista")

# EDITAR
@app.route("/editar/<int:id>", methods=["GET","POST"])
def editar(id):
    con = sqlite3.connect("database.db")
    cur = con.cursor()

    if request.method == "POST":
        datos = (
            request.form["codigo"],
            request.form["producto"],
            request.form["cliente"],
            request.form["cantidad"],
            id
        )
        cur.execute("UPDATE pedidos SET codigo=?,producto=?,cliente=?,cantidad=? WHERE id=?", datos)
        con.commit()
        con.close()
        return redirect("/lista")

    cur.execute("SELECT * FROM pedidos WHERE id=?", (id,))
    p = cur.fetchone()
    con.close()

    return render_template("editar.html", p=p)

# PDF
@app.route("/pdf")
def pdf():
    con = sqlite3.connect("database.db")
    cur = con.cursor()
    cur.execute("SELECT codigo,producto,cliente,cantidad FROM pedidos")
    datos = cur.fetchall()
    con.close()

    archivo = "pedidos.pdf"
    doc = SimpleDocTemplate(archivo)
    tabla = Table([["Código","Producto","Cliente","Cantidad"]] + datos)
    doc.build([tabla])

    return send_file(archivo, as_attachment=True)

if __name__ == "__main__":
    app.run()