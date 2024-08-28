
# Generated from ML Pipeline "cauldron-offboarding-test"

from airflow.models import DAG
from datetime import datetime, timedelta

from chimeracli.chimeracli_mlp_experiment_impl import ChimeraCliExperimentCreationOperator
from chimeracli.chimeracli_mlp_data_impl import ChimeraCliSparkJobCreationOperator, \
    ChimeraCliSandboxJobCreationOperator, ChimeraCliDataValidationCreationOperator, \
    ChimeraCliDataPreparationCreationOperator, ChimeraCliTrainingJobCreationOperator, \
    ChimeraCliBatchInferOperator
from chimeracli.chimeracli_mlp_model_impl import ModelServingSubmitOperator, ModelServingLandOperator, \
    ChimeraCliMLModelBankOperator

default_args = {
    "owner": "itn.hung.do",
    "start_date": datetime(2024, 8, 26),
    "email": ["itn.hung.do@grabtaxi.com"],
    "email_on_failure": False,
    "email_on_retry": False,
    "retries": 3,
    "retry_delay": timedelta(minutes=3),
    "queue": "default"
}

dag = DAG('cauldron-offboarding-test',
          default_args=default_args,
          max_active_runs=1,
          schedule_interval='20 01 * * *',
          params={}
)

PIPELINE_NAME = "cauldron-offboarding-test"
EXPERIMENT_NAME = "cauldron-offboarding-test-{{ ds_nodash }}"

experiment = ChimeraCliExperimentCreationOperator(
    task_id="experiment-cauldron-offboarding-test",
    name=EXPERIMENT_NAME,
    pipeline=PIPELINE_NAME,
    cloud="aws",
    dag=dag, 
)

spark_store_deactivated_accounts = ChimeraCliSparkJobCreationOperator(
    task_id="spark-store-deactivated-accounts",
    pipeline=PIPELINE_NAME,
    experiment=EXPERIMENT_NAME,
    job_name="store-deactivated-accounts",
    cloud="aws",
    dag=dag,
)

experiment >> spark_store_deactivated_accounts