from flask_login import UserMixin
from bson import ObjectId
from services.db import coleccion_usuarios

class User(UserMixin):
    def __init__(self, user_doc):
        self.id = str(user_doc["_id"])
        self.nombre_local = user_doc["nombre_local"]
        self.ubicacion = user_doc["ubicacion"]
        self.ip_camara = user_doc["ip_camara"]

def get_user_by_id(user_id):
    user_doc = coleccion_usuarios.find_one({"_id": ObjectId(user_id)})
    if user_doc:
        return User(user_doc)
    return None

def get_user_by_nombre(nombre_local):
    return coleccion_usuarios.find_one({"nombre_local": nombre_local})
