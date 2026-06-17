import psycopg2
import os
from dotenv import load_dotenv

load_dotenv()

def get_connection():
    try:
        db_name = os.getenv("DB_NAME", "").strip()
        db_user = os.getenv("DB_USER", "").strip()
        db_pass = os.getenv("DB_PASS", "").strip()
        db_host = os.getenv("DB_HOST", "").strip()
        db_port = os.getenv("DB_PORT", "").strip()

        dsn = f"dbname='{db_name}' user='{db_user}' password='{db_pass}' host='{db_host}' port='{db_port}'"

        conn = psycopg2.connect(dsn)
        
        conn.set_client_encoding('UTF8')
        
        print("Conexão com o PostgreSQL realizada com sucesso!")
        return conn
    except Exception as e:
        print(f"Erro ao conectar no banco: {repr(e)}")
        return None