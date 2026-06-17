from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from database.db_connection import get_connection
import psycopg2.extras

app = FastAPI(title="Alerta-Rio API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/crimes/mapa")
def get_mapa():
    conn = get_connection()
    if not conn:
        return {"error": "Falha na conexão com o banco de dados"}
    try:
        cursor = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
        query = """
            SELECT 
                municipio, 
                latitude, 
                longitude, 
                SUM(tipo_soma) as total,
                json_object_agg(tipo_crime, tipo_soma) as detalhes
            FROM (
                SELECT 
                    municipio, 
                    latitude, 
                    longitude, 
                    tipo_crime, 
                    SUM(quantidade) as tipo_soma
                FROM manchas_criminais
                GROUP BY municipio, latitude, longitude, tipo_crime
            ) AS subconsulta
            GROUP BY municipio, latitude, longitude
            ORDER BY total DESC;
        """
        cursor.execute(query)
        rows = cursor.fetchall()
        return [dict(row) for row in rows]
    except Exception as e:
        return {"error": str(e)}
    finally:
        cursor.close()
        conn.close()

@app.get("/crimes/detalhes/{municipio}")
def get_detalhes(municipio: str):
    conn = get_connection()
    if not conn:
        return {"error": "Falha na conexão com o banco de dados"}
    try:
        cursor = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
        query = """
            SELECT 
                TO_CHAR(data_referencia, 'MM/YYYY') as periodo, 
                tipo_crime, 
                SUM(quantidade) as quantidade 
            FROM manchas_criminais 
            WHERE municipio = %s
            GROUP BY TO_CHAR(data_referencia, 'MM/YYYY'), tipo_crime, data_referencia
            ORDER BY data_referencia DESC, quantidade DESC;
        """
        cursor.execute(query, [municipio.upper()])
        rows = cursor.fetchall()
        return [dict(row) for row in rows]
    except Exception as e:
        return {"error": str(e)}
    finally:
        cursor.close()
        conn.close()

@app.get("/")
def read_root():
    return {
        "status": "API Alerta-Rio — Sistema Monitor de Segurança Pública",
        "endpoints_validos": ["/crimes/mapa", "/crimes/detalhes/{municipio}"]
    }