# config/database.py
import psycopg2
from psycopg2 import sql
import os
from dotenv import load_dotenv

load_dotenv()  # Carga las variables de entorno desde .env

def get_connection():
    #Devuelve una conexión a PostgreSQL usando variables de entorno.
    return psycopg2.connect(
        dbname=os.getenv('DB_NAME'),
        user=os.getenv('DB_USER'),
        password=os.getenv('DB_PASSWORD'),
        host=os.getenv('DB_HOST', 'localhost'),
        port=os.getenv('DB_PORT', '5432')
    )

def get_user_by_email(email):
    #Busca un usuario por su email. Retorna el registro como diccionario o None.
    conn = get_connection()
    cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    cur.execute("SELECT * FROM users WHERE email = %s;", (email,))
    user = cur.fetchone()
    cur.close()
    conn.close()
    return user

def create_user(email, password_hash, full_name=None):
    #Crea un nuevo usuario. Retorna el ID del usuario creado o lanza excepción.
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        """INSERT INTO users (email, password_hash, full_name)
           VALUES (%s, %s, %s) RETURNING id;""",
        (email, password_hash, full_name)
    )
    user_id = cur.fetchone()[0]
    conn.commit()
    cur.close()
    conn.close()
    return user_id