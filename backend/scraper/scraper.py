import requests
import pandas as pd
import io
import json
import os
from database.db_connection import get_connection
from psycopg2.extras import execute_values

def carregar_coordenadas():
    caminho = os.path.join(os.path.dirname(__file__), 'coordenadas.json')
    try:
        with open(caminho, 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        return {}

def run_scraper():
    file_url = "https://www.ispdados.rj.gov.br/Arquivos/BaseDPEvolucaoMensalCisp.csv"
    response = requests.get(file_url)
    content = response.content.decode('iso-8859-1')
    df = pd.read_csv(io.StringIO(content), sep=';')

    dict_coords = carregar_coordenadas()
    col_municipio = 'munic' if 'munic' in df.columns else 'fmun'
    
    crimes_monitorados = {
        'roubo_veiculo': 'Roubo de Veiculo',
        'roubo_celular': 'Roubo de Celular',
        'roubo_carga': 'Roubo de Carga',
        'roubo_rua': 'Roubo de Rua'
    }

    df_filtrado = df[df['ano'] >= 2022] 
    mapa_acumulador = {}

    for _, row in df_filtrado.iterrows():
        municipios_raw = str(row[col_municipio]).upper()
        lista_municipios = municipios_raw.split(';')
        data_atual = f"{row['ano']}-{str(row['mes']).zfill(2)}-01"
        bairro_dp = f"DP {row['cisp']}"
        
        for m in lista_municipios:
            nome_m = m.strip()
            if nome_m in dict_coords:
                coord = dict_coords[nome_m]
                for col_csv, nome_crime in crimes_monitorados.items():
                    qtd = row.get(col_csv, 0)
                    if qtd > 0:
                        chave = (bairro_dp, nome_m, nome_crime, data_atual)
                        if chave not in mapa_acumulador:
                            mapa_acumulador[chave] = {
                                "qtd": 0,
                                "lat": float(coord['lat']),
                                "lon": float(coord['lon'])
                            }
                        mapa_acumulador[chave]["qtd"] += int(qtd)

    lista_de_tuplas = []
    for (bairro, muni, crime, data), info in mapa_acumulador.items():
        lista_de_tuplas.append((bairro, muni, crime, info["qtd"], data, info["lat"], info["lon"]))

    if len(lista_de_tuplas) > 0:
        conn = get_connection()
        if conn:
            try:
                cursor = conn.cursor()
                query = """
                    INSERT INTO manchas_criminais 
                    (bairro, municipio, tipo_crime, quantidade, data_referencia, latitude, longitude)
                    VALUES %s;
                """
                execute_values(cursor, query, lista_de_tuplas)
                conn.commit()
            except Exception as e:
                conn.rollback()
            finally:
                cursor.close()
                conn.close()

if __name__ == "__main__":
    run_scraper()