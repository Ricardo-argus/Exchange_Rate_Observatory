import os
import pandas as pd
import numpy as np
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import insert

CONN_STR = (
    f"postgresql+psycopg2://{os.getenv('POSTGRES_USER')}:{os.getenv('POSTGRES_PASSWORD')}"
    f"@{os.getenv('POSTGRES_HOST')}:{os.getenv('POSTGRES_PORT')}/{os.getenv('POSTGRES_DB')}"
)
engine = sa.create_engine(CONN_STR)

def gold_euro_data():
    #Lê dados da tabela Silver euro cambio
    gold_eur = pd.read_sql("SELECT * FROM public.silver_euro_cambio ORDER BY datahoracotacao", engine)

    # Garante parsing de datetime antes de extrair data e hora
    gold_eur["datahoracotacao"] = pd.to_datetime(gold_eur["datahoracotacao"])

    # Modificar Coluna Datahoracotacao > Data
    gold_eur["data_publicacao"] = gold_eur["datahoracotacao"].dt.date

    # Criar nova coluna para armazenar Hora
    gold_eur["hora_publicacao"] = gold_eur["datahoracotacao"].dt.strftime("%H:%M:%S")

    # Estipular 2 casas decimais para Cotacoes
    gold_eur['cotacao_compra'] = gold_eur['cotacao_compra'].round(2)
    gold_eur['cotacao_venda'] =  gold_eur['cotacao_venda'].round(2)

    # Arredondar variacoes para 3 casas decimais
    gold_eur["variacao_venda"] = gold_eur["variacao_venda"].round(3)
    gold_eur["variacao_compra"] = gold_eur["variacao_compra"].round(3)
    gold_eur["variacao_pct_venda"] = gold_eur["variacao_pct_venda"].round(3)
    gold_eur["variacao_pct_compra"] = gold_eur["variacao_pct_compra"].round(3)

    # eliminar coluna antiga
    gold_eur = gold_eur.drop(columns=["datahoracotacao"])

    #eliminar registros incosistentes de boletim
    gold_eur = gold_eur.drop_duplicates(subset=["data_publicacao", "hora_publicacao"], keep="last")
    

    # Selecionar Colunas
    gold_eur = gold_eur[[
    "data_publicacao", "hora_publicacao", "cotacao_compra", "cotacao_venda",
    "variacao_venda", "variacao_compra", "variacao_pct_venda", "variacao_pct_compra",
    "tipoboletim"
    ]]


    rows = gold_eur.to_dict(orient="records")
    
    metadata = sa.MetaData()
    
    # Define a tabela gold_euro_cambio (cria se não existir)
    gold_euro = sa.Table(
        "gold_euro_cambio",
        metadata,
        sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
        sa.Column("cotacao_compra", sa.Numeric(10,2), nullable=False),
        sa.Column("cotacao_venda", sa.Numeric(10,2), nullable=False),
        sa.Column("data_publicacao", sa.Date, nullable=False),
        sa.Column("hora_publicacao", sa.Time, nullable=False),
        sa.Column("variacao_venda", sa.Numeric(10,3)),
        sa.Column("variacao_compra", sa.Numeric(10,3)),
        sa.Column("variacao_pct_venda", sa.Numeric(10,3)),
        sa.Column("variacao_pct_compra", sa.Numeric(10,3)),
        sa.Column("tipoboletim", sa.String(50)),
        sa.UniqueConstraint("data_publicacao", "hora_publicacao", name="uq_gold_euro_data_hora"),
        extend_existing=True
    )

    # Cria Tabela se nao existir
    metadata.create_all(engine)

    with engine.begin() as conn:

    # Faz o upsert das colunas
        stmt = insert(gold_euro).values(rows)

        stmt = stmt.on_conflict_do_update(
            index_elements=["data_publicacao", "hora_publicacao"],
            set_={
                "cotacao_compra": stmt.excluded.cotacao_compra,
                "cotacao_venda": stmt.excluded.cotacao_venda,
                "tipoboletim": stmt.excluded.tipoboletim,
                "variacao_venda": stmt.excluded.variacao_venda,
                "variacao_compra": stmt.excluded.variacao_compra,
                "variacao_pct_venda": stmt.excluded.variacao_pct_venda,
                "variacao_pct_compra": stmt.excluded.variacao_pct_compra
            }
        )
        conn.execute(stmt)