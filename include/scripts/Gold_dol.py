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

def gold_dol_data():
    #Lê dados da tabela Silver dolar cambio
    df = pd.read_sql("SELECT * FROM public.silver_dol_cambio ORDER BY datahoracotacao", engine)

    # Modificar Coluna Datahoracotacao > Data
    df["data_publicacao"] = df["datahoracotacao"].dt.date

    # Criar nova coluna para armazenar Hora
    df["hora_publicacao"] = df["datahoracotacao"].dt.time

    # Estipular 2 casas decimais para Cotacoes
    df['cotacao_compra'] = df['cotacao_compra'].round(2)
    df['cotacao_venda'] =  df['cotacao_venda'].round(2)

    # Arredondar variacoes para 3 casas decimais
    df["variacao_venda"] = df["variacao_venda"].round(3)
    df["variacao_compra"] = df["variacao_compra"].round(3)
    df["variacao_pct_venda"] = df["variacao_pct_venda"].round(3)
    df["variacao_pct_compra"] = df["variacao_pct_compra"].round(3)

    # eliminar coluna antiga
    df = df.drop(columns=["datahoracotacao"])

    # Selecionar Colunas
    df = df[[
    "id", "data_publicacao", "hora_publicacao", "cotacao_compra", "cotacao_venda",
    "variacao_venda", "variacao_compra", "variacao_pct_venda", "variacao_pct_compra",
    "tipoboletim"
    ]]

    rows = df.to_dict(orient="records")
    
    metadata = sa.MetaData()
    
    # Define a tabela gold_dol_cambio (cria se não existir)
    gold_dol = sa.Table(
        "gold_dol_cambio",
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
        sa.UniqueConstraint("data_publicacao", "hora_publicacao", name="uq_gold_dol_data_hora"),
        extend_existing=True
    )

    # Cria Tabela se nao existir
    metadata.create_all(engine)

    with engine.begin() as conn:

        stmt = insert(gold_dol).values(rows)

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