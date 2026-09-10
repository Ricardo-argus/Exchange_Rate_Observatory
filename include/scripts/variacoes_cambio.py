import os
import pandas as pd
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import insert

CONN_STR = (
    f"postgresql+psycopg2://{os.getenv('POSTGRES_USER')}:{os.getenv('POSTGRES_PASSWORD')}"
    f"@{os.getenv('POSTGRES_HOST')}:{os.getenv('POSTGRES_PORT')}/{os.getenv('POSTGRES_DB')}"
)
engine = sa.create_engine(CONN_STR)

def joins_cambio():
    # Lê os dados das tabelas Gold
    df_dol = pd.read_sql("SELECT * FROM public.gold_dol_cambio ORDER BY data_publicacao", engine)
    df_euro = pd.read_sql("SELECT * FROM public.gold_euro_cambio ORDER BY data_publicacao", engine)

    # Deleta registros duplicados de boletim + data 
    df_dol = df_dol.drop_duplicates(subset=["data_publicacao", "tipoboletim"], keep="last")
    df_euro = df_euro.drop_duplicates(subset=["data_publicacao", "tipoboletim"], keep="last")

    # Faz o merge pelo campo de data
    df = pd.merge(
        df_dol,
        df_euro,
        left_on=["data_publicacao", "tipoboletim"],
        right_on=["data_publicacao", "tipoboletim"],
        how="inner",
        suffixes=("_dol", "_euro")
    )

    # Seleciona e renomeia colunas
    df = df[[
        "data_publicacao", "tipoboletim", "hora_publicacao_dol", "hora_publicacao_euro",
        "cotacao_venda_dol", "cotacao_venda_euro",
        "cotacao_compra_dol", "cotacao_compra_euro"
    ]]

    # Calcula variações entre moedas
    df["variacao_compra_moeda"] = (df["cotacao_compra_dol"] - df["cotacao_compra_euro"]).round(3)
    df["variacao_venda_moeda"] = (df["cotacao_venda_dol"] - df["cotacao_venda_euro"]).round(3)

    # Registra dados 
    rows = df.to_dict(orient="records")

    metadata = sa.MetaData()

    # Define a tabela consolidada
    cambio_eur_usd = sa.Table(
        "cambio_eur_usd",
        metadata,
        sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
        sa.Column("data_publicacao", sa.Date, nullable=False),
        sa.Column("hora_publicacao_dol", sa.Time, nullable=False),
        sa.Column("hora_publicacao_euro", sa.Time, nullable=False),
        sa.Column("cotacao_venda_dol", sa.Numeric(10,2)),
        sa.Column("cotacao_venda_euro", sa.Numeric(10,2)),
        sa.Column("cotacao_compra_dol", sa.Numeric(10,2)),
        sa.Column("cotacao_compra_euro", sa.Numeric(10,2)),
        sa.Column("variacao_compra_moeda", sa.Numeric(10,3)),
        sa.Column("variacao_venda_moeda", sa.Numeric(10,3)),
        sa.Column("tipoboletim", sa.String(50), nullable=False), 
        sa.UniqueConstraint("data_publicacao", "tipoboletim", name="unq_data_boletim"),
        extend_existing=True
    )

    metadata.create_all(engine)

    with engine.begin() as conn:

    # Faz o upsert
        stmt = insert(cambio_eur_usd).values(rows)

        stmt = stmt.on_conflict_do_update(
            index_elements=["data_publicacao", "tipoboletim"],
            set_={
                "hora_publicacao_dol" : stmt.excluded.hora_publicacao_dol,
                "hora_publicacao_euro" : stmt.excluded.hora_publicacao_euro,
                "cotacao_venda_dol": stmt.excluded.cotacao_venda_dol,
                "cotacao_venda_euro": stmt.excluded.cotacao_venda_euro,
                "cotacao_compra_dol": stmt.excluded.cotacao_compra_dol,
                "cotacao_compra_euro": stmt.excluded.cotacao_compra_euro,
                "variacao_compra_moeda": stmt.excluded.variacao_compra_moeda,
                "variacao_venda_moeda": stmt.excluded.variacao_venda_moeda
            }
        )
        conn.execute(stmt)