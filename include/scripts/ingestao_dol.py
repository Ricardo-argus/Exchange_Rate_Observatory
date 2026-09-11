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

bronze_dol_cambio = sa.Table(
        'bronze_dol_cambio',
        metadata,
        sa.Column('id', sa.Integer, primary_key=True, autoincrement=True),
        sa.Column("cotacao_compra", sa.Numeric(10,4)),
        sa.Column("cotacao_venda", sa.Numeric(10,4)),
        sa.Column("datahoracotacao", sa.TIMESTAMP, nullable=False, unique=True),
        sa.Column('tipoboletim', sa.String)
)

metadata.create_all(engine)

def ingest_data():

    bronze_dol = pd.read_excel("/opt/airflow/excel_analyses/Advanced_Imported_Analyses.xlsm", sheet_name="Main_Macros", header=None, engine="openpyxl")
    
    # coluna'url_fechamento_API'
    url_fechamento = bronze_dol.iloc[30, 2]

    url_abertura = bronze_dol.iloc[30, 5]

    response = requests.get(url_fechamento).json()

    rows = []
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

    # Junta dados abertura e fechamento
    bronze_dol = pd.DataFrame(rows)

    # Carrega a tabela
    table = sa.Table("bronze_dol_cambio", sa.MetaData(), autoload_with=engine)

    with engine.begin() as conn:

        # Faz o upsert (insere e atualiza se já existir)
        stmt = insert(table).values(bronze_dol.to_dict(orient="records"))
        stmt = stmt.on_conflict_do_update(
            index_elements=["datahoracotacao"],
            set_={
                "cotacao_compra": stmt.excluded.cotacao_compra,
                "cotacao_venda": stmt.excluded.cotacao_venda,
                "tipoboletim": stmt.excluded.tipoboletim
            }
        )
        conn.execute(stmt)