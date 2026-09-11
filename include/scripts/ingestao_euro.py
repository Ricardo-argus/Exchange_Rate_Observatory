import os
import requests
import sqlalchemy as sa
from datetime import datetime
from sqlalchemy.dialects.postgresql import insert
import pandas as pd

# Usa a mesma string de conexão definida no docker-compose
CONN_STR = (
    f"postgresql+psycopg2://{os.getenv('POSTGRES_USER')}:{os.getenv('POSTGRES_PASSWORD')}"
    f"@{os.getenv('POSTGRES_HOST')}:{os.getenv('POSTGRES_PORT')}/{os.getenv('POSTGRES_DB')}"
)

engine = sa.create_engine(CONN_STR)
metadata = sa.MetaData()

bronze_euro_cambio = sa.Table(
        'bronze_euro_cambio',
        metadata,
        sa.Column('id', sa.Integer, primary_key=True, autoincrement=True),
        sa.Column("cotacao_compra", sa.Numeric(10,4)),
        sa.Column("cotacao_venda", sa.Numeric(10,4)),
        sa.Column("datahoracotacao", sa.TIMESTAMP, nullable=False, unique=True),
        sa.Column('tipoboletim', sa.String)
)

metadata.create_all(engine)  # cria a tabela se não existir

def ingest_euro_data():

    # Carrega o Excel
    bronze_euro = pd.read_excel("/opt/airflow/excel_analyses/Advanced_Imported_Analyses.xlsm", sheet_name="Main_Macros", header=None, engine="openpyxl")
    
    # Coluna 'url_fechamento_API'
    url_fechamento = bronze_euro.iloc[24, 2]

    # Coluna url_abertura API
    url_abertura = bronze_euro.iloc[24, 5]

    rows = []

    # Consulta API Fechamento
    response = requests.get(url_fechamento, timeout=30)

    response.raise_for_status()

    response = response.json()

    for item in response["value"]:
        rows.append({
            "cotacao_compra": float(item["cotacaoCompra"]),
            "cotacao_venda": float(item["cotacaoVenda"]),
            "datahoracotacao": datetime.strptime(item["dataHoraCotacao"], "%Y-%m-%d %H:%M:%S.%f"),
            "tipoboletim": str(item["tipoBoletim"])
        })

    # Consulta API Abertura
    response = requests.get(url_abertura, timeout=30)

    response.raise_for_status()

    response = response.json()

    for item in response["value"]:
        rows.append({
            "cotacao_compra": float(item["cotacaoCompra"]),
            "cotacao_venda": float(item["cotacaoVenda"]),
            "datahoracotacao": datetime.strptime(item["dataHoraCotacao"], "%Y-%m-%d %H:%M:%S.%f"),
            "tipoboletim": str(item["tipoBoletim"])
    })

    # Transforma em Dataframe dados da URLs
    bronze_euro = pd.DataFrame(rows)
    
    # Carrega a Tabela 
    table = sa.Table("bronze_euro_cambio", sa.MetaData(), autoload_with=engine)

    # Faz o upsert usando datahoracotacao como chave única
    with engine.begin() as conn:

        # Faz o upsert 
        stmt = insert(table).values(bronze_euro.to_dict(orient="records"))
        stmt = stmt.on_conflict_do_update(
            index_elements=["datahoracotacao"],  
            set_={
                "cotacao_compra": stmt.excluded.cotacao_compra,
                "cotacao_venda": stmt.excluded.cotacao_venda,
                "tipoboletim": stmt.excluded.tipoboletim
            }
        )
        conn.execute(stmt)