# OBSERVATORIO_CAMBIO

##  Overview
O **Observatório de Câmbio** é um projeto de análise e monitoramento de variações cambiais, integrando **Airflow** para orquestração de pipelines e **dbt (Data Build Tool)** para transformação e modelagem de dados.  
O objetivo é fornecer insights sobre taxas de câmbio, detectar anomalias e gerar métricas consolidadas em diferentes camadas de dados (**silver** e **gold**).

---

##  Inicialização do Projeto

### Pré-requisitos
- **Python 3.9+**
- **Apache Airflow**
- **dbt-core**
- **docker personal**
- **Banco de dados PostgreSQL**
- **Microsoft Excel**
- **ODBC 3.9 for Postgres** 

### Passos de Setup
1. Clone o repositório:
   ```bash
   git clone https://github.com/Ricardo-argus/observatorio_cambio
   cd OBSERVATORIO_CAMBIO

### Configure o ambiente virtual

bash

python -m venv venv
source venv/bin/activate   # Linux/Mac

# Instale as dependências:

pip install -r requirements.txt

obs: Caso as imagens já estejam armazenadas no Dockerfile, não se torna necessário o uso do requirements

# Configurações

Ajuste o arquivo airflow_settings.yaml e inicialize o banco de metadados do Airflow

Bash

airflow db init
airflow webserver
airflow scheduler

Ajustar documento docker-compose.yaml e Dockerfile(inserindo pacotes a serem utilizados)

Inserir Váriaveis de ambiente no .env para reconhecer conexão 

## Configurar dbt 

Ajuste os arquivos dbt_project.yml e profiles.yml

execute os modelos:

bash 

dbt run
dbt test

# ESTRUTURA DO PROJETO

```
OBSERVATORIO_CAMBIO/
│
├── dags/
│   ├── monitoramento_dolar.py
│   └── graficos_gen.py
│
├── include/
│   ├── analysys_dbt/
│   │   ├── macros/
│   │   ├── models/
│   │   │   ├── silver/
│   │   │   └── gold/
│   │   ├── snapshots/
│   │   └── tests/
│   │
│   └── scripts/
│       ├── graficos.py
│       ├── ingestao_dol.py
│       ├── ingestao_euro.py
│       ├── processamento_dol.py
│       ├── processamento_euro.py
│       └── variacoes_cambio.py
        

## Airflow DAGS

As principais DAGs implementadas são:
- Monitoramento do Dólar (monitoramento_dolar.py)
    - Coleta dados de câmbio e aplica transformações iniciais.
- Geração de Gráficos (graficos_gen.py)
    - Produz relatórios visuais e métricas consolidadas.

# DBT 

## MACROS 

Macros para validação de duplicados, preencher valores nulos com COALESCE (0) e Validação da % de variação entre cotações

## MODELOS

Modelos para obter media de valores, variações de compra e venda, obter revenue entre outros...

## EXCEL VBA MACROS

Uma Planilha excel fará a atualização do link da API do BACEN para atualizar diariamente o câmbio do euro e dolar, além de importar tabelas, criar gráficos e tabelas dinâmicas com as tabelas criadas pelo orquestrador utilizando os scripts python.


