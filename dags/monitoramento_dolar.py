from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.operators.bash import BashOperator
from airflow.operators.trigger_dagrun import TriggerDagRunOperator
from datetime import datetime, timedelta
from include.scripts.ingestao_dol import ingest_data
from include.scripts.ingestao_euro import ingest_euro_data
from include.scripts.processamento_dol import process_dol_data
from include.scripts.processamento_euro import process_euro_data
from include.scripts.variacoes_cambio import joins_cambio
from airflow.utils.task_group import TaskGroup

with DAG(
    dag_id="monitoramento_cambial",
    start_date=datetime(2022,1,1),
    schedule_interval = "@daily",
    catchup=False
) as dag:
    
    with TaskGroup("pipeline_dolar") as pipeline_dolar:
        t1 = PythonOperator(task_id="ingestao_dol", python_callable = ingest_data)
        t3 = PythonOperator(task_id="processamento_dol", python_callable=process_dol_data)
        t1 >> t3


    with TaskGroup("pipeline_euro") as pipeline_euro:
        t2 = PythonOperator(task_id="ingestao_euro", python_callable = ingest_euro_data)
        t4 = PythonOperator(task_id="processamento_euro", python_callable=process_euro_data)
        t2 >> t4

    join_cambios = PythonOperator(task_id="join_cambial", python_callable=joins_cambio)


    with TaskGroup("dbt_process") as dbt_process:
        rodar_dbt = BashOperator(
        task_id = "dbt_run",
        bash_command="cd /opt/airflow/include/analysys_dbt && dbt run --profiles-dir /opt/airflow/include/analysys_dbt"
        )

        teste_models = BashOperator(
        task_id = "dbt_test",
        bash_command="cd /opt/airflow/include/analysys_dbt && dbt test --profiles-dir /opt/airflow/include/analysys_dbt"
        )

        criar_DAG_models = BashOperator(
        task_id = "dbt_dag",
        bash_command = "cd /opt/airflow/include/analysys_dbt && dbt docs generate --profiles-dir /opt/airflow/include/analysys_dbt"
        )

        rodar_dbt >> teste_models >> criar_DAG_models

    trigger_graficos = TriggerDagRunOperator(
        task_id = "trigger_graficos_dag",
        trigger_dag_id = "graficos_dag"
    )


    [pipeline_dolar, pipeline_euro] >> join_cambios >> dbt_process >> trigger_graficos 
