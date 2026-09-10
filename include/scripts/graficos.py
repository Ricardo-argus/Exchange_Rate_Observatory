import os
import pandas as pd
import numpy as np
import sqlalchemy as sa
import seaborn as sns
import matplotlib.pyplot as plt



CONN_STR = (
    f"postgresql+psycopg2://{os.getenv('POSTGRES_USER')}:{os.getenv('POSTGRES_PASSWORD')}"
    f"@{os.getenv('POSTGRES_HOST')}:{os.getenv('POSTGRES_PORT')}/{os.getenv('POSTGRES_DB')}"
)
engine = sa.create_engine(CONN_STR)

def graph_py(output_dir="/opt/airflow/output_charts"):

    os.makedirs(output_dir, exist_ok=True)

    df = pd.read_sql("SELECT * FROM public.cambio_eur_usd ORDER BY id DESC", engine)

    #Grafico de linha cotacao dol

    sns.lineplot(data=df, x="data_publicacao", y="cotacao_venda_dol")
    plt.title("Cotação de Venda do Dólar ao longo do tempo")
    plt.xticks(rotation=45)
    plt.tight_layout()
    plt.savefig(os.path.join(output_dir, "cotacao_vendadol.png"))
    plt.close()

    #Histograma variacao

    sns.histplot(df["variacao_compra_moeda"], bins=30, kde=True)
    plt.title("Distribuição da variação de compra da moeda")
    plt.tight_layout()
    plt.savefig(os.path.join(output_dir, "hist_variacao.png"))
    plt.close()

def graph_sql(output_dir="/opt/airflow/output_charts"):

    os.makedirs(output_dir, exist_ok=True)

    query_sql = """
        SELECT DATE_TRUNC('month', data_publicacao) AS mes,
            AVG(cotacao_venda_dol) AS media_dolar,
            AVG(cotacao_venda_euro) AS media_euro
        FROM public.cambio_eur_usd
        WHERE data_publicacao >= '2025-09-01'
        GROUP by mes
        ORDER BY mes
    """
    df = pd.read_sql(query_sql, engine)

    # Formata a coluna 'mes' para apenas Ano-Mês ou Mês/Ano
    df["mes"] = pd.to_datetime(df["mes"]).dt.strftime("%Y-%m")

    # Plota o gráfico (xlabel="" remove a legenda 'mes' do rodapé)
    ax = df.plot(x="mes", y=["media_dolar", "media_euro"], kind="bar", xlabel="")
    
    plt.title("Média mensal das cotações de venda (USD vs EUR)")
    plt.xticks(rotation=45, ha="right")
    plt.tight_layout()
    plt.savefig(os.path.join(output_dir, "grafico_medias_mensais.png"))
    plt.close()
