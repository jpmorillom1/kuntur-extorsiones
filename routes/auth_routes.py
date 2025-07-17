from flask import Blueprint, render_template, request, redirect, session
from bson import ObjectId
from werkzeug.security import generate_password_hash, check_password_hash
from services.db import coleccion_usuarios
from services.db import coleccion_alertas

auth_bp = Blueprint('auth', __name__)

@auth_bp.route("/", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        nombre = request.form["nombre_local"]
        password = request.form["password"]

        usuario = coleccion_usuarios.find_one({"nombre_local": nombre})
        if usuario and check_password_hash(usuario["password"], password):
            session["usuario_id"] = str(usuario["_id"])
            session["ip_camara"] = usuario["ip_camara"]
            session["nombre_local"] = usuario["nombre_local"]
            session['ubicacion'] = usuario["ubicacion"]
            session['latitud'] = usuario["latitud"]
            session['longitud'] = usuario["longitud"]
            return redirect("/panel")
        else:
            return render_template("login.html", error="Credenciales incorrectas")

    return render_template("login.html")


@auth_bp.route("/registrar", methods=["GET", "POST"])
def registrar():
    if request.method == "POST":
        nombre = request.form["nombre_local"]
        ubicacion = request.form["ubicacion"]
        ip_camara = request.form["ip_camara"]
        lat = request.form.get("latitud")
        lng = request.form.get("longitud")
        password = generate_password_hash(request.form["password"])

        if coleccion_usuarios.find_one({"nombre_local": nombre}):
            return render_template("registro.html", error="El nombre del local ya existe")

        coleccion_usuarios.insert_one({
            "nombre_local": nombre,
            "ubicacion": ubicacion,
            "ip_camara": ip_camara,
            "latitud": float(lat) if lat else None,
            "longitud": float(lng) if lng else None,
            "password": password
        })

        return redirect("/")

    return render_template("registro.html")


@auth_bp.route("/panel")
def panel():
    if "usuario_id" not in session:
        return redirect("/")

    usuario = coleccion_usuarios.find_one({"_id": ObjectId(session["usuario_id"])})
    if not usuario:
        return redirect("/")

    return render_template(
        "index.html",
        ip_camera=usuario["ip_camara"],
        nombre_local=usuario["nombre_local"],
        ubicacion=usuario["ubicacion"],
    )


