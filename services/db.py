from pymongo import MongoClient
from dotenv import load_dotenv
import os

load_dotenv()

client = MongoClient(os.getenv("MONGO_URI"))
db = client["kuntur-extorsiones"]

coleccion_usuarios = db["user"]
coleccion_alertas = db["alert"]
