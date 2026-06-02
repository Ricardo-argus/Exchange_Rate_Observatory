# Customização da imagem do Airflow (para instalar dbt e pandas)
FROM apache/airflow:2.7.0

# Copia requirements para dentro da imagem
COPY requirements.txt .

# Instala todas as libs de uma vez
RUN pip install --no-cache-dir -r requirements.txt