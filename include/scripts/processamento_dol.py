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

def process_dol_data():
    # Lê os dados da tabela bronze_euro_cambio
    df = pd.read_sql("SELECT * FROM public.bronze_dol_cambio ORDER BY datahoracotacao", engine)

    # Calcula variações
    df["variacao_venda"] = (df["cotacao_venda"] - df["cotacao_venda"].shift(1)).round(2)
    df["variacao_compra"] = (df["cotacao_compra"] - df["cotacao_compra"].shift(1)).round(2)
    df["variacao_pct_venda"] = (df["cotacao_venda"].pct_change() * 100).round(2)
    df["variacao_pct_compra"] = (df["cotacao_compra"].pct_change() * 100).round(2)

    df = df.fillna(0)  

    rows = df.to_dict(orient="records")

    metadata = sa.MetaData()

    # Define a tabela silver_dol_cambio (cria se não existir)
    silver_dol = sa.Table(
        "silver_dol_cambio",
        metadata,
        sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
        sa.Column("cotacao_compra", sa.Numeric(10,4), nullable=False),
        sa.Column("cotacao_venda", sa.Numeric(10,4), nullable=False),
        sa.Column("datahoracotacao", sa.TIMESTAMP, nullable=False, unique=True),
        sa.Column("variacao_venda", sa.Numeric(10,4)),
        sa.Column("variacao_compra", sa.Numeric(10,4)),
        sa.Column("variacao_pct_venda", sa.Numeric(10,4)),
        sa.Column("variacao_pct_compra", sa.Numeric(10,4)),
        sa.Column("tipoboletim", sa.String(50)),
        extend_existing=True
    )

    # cria a tabela se não existir
    metadata.create_all(engine)  

    with engine.begin() as conn:
        # Apaga os dados antigos
        conn.execute(sa.text("DELETE FROM silver_dol_cambio"))

    # Faz o upsert
        stmt = insert(silver_dol).values(rows)
        stmt = stmt.on_conflict_do_update(
            index_elements=["datahoracotacao"],
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