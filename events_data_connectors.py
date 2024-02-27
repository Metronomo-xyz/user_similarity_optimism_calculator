from abc import ABC, abstractmethod
import pandas as pd
from dotenv import load_dotenv
from google.cloud import bigquery
from google.oauth2 import service_account

class DataConnector(ABC):
    @abstractmethod
    def getData(self) -> pd.DataFrame:
        pass


class MetronomoOptimismTXBigQueryConnector(DataConnector):
    def __init__(self,
        dates,
        project,
        dataset,
        token_json_path=None):
        """
        Parameters
        ----------
        dates: list[datetime.Date]
            dates range to retrieve the data. Should be iterable of datetime.date type
        project: str
            name of the project to get data from. Either provided or got from .static_env file, variable MetronomoOptimismTXBigQueryConnector_DEFAULT_PROJECT
        dataset: str
            name of the dataset to get data from. Either provided or got from .static_env file, variable MetronomoOptimismTXBigQueryConnector_DEFAULT_dataset
        token_json_path: str
            path to token json file. Either provided or got from .env file, variable MetronomoTXCloudStorageConnector_TOKEN_JSON_PATH
        """

        load_dotenv("user_similarity_optimism_calculator/static_config.env")

        self.token_json_path = token_json_path
        self.credentials = service_account.Credentials.from_service_account_file(self.token_json_path)
        self.client = bigquery.Client()

        #self.client = bigquery.Client(credentials= self.credentials,project=project)

        self.query_t = """
            SELECT * 
            FROM `web3advertisement.optimism_data.transactions_full_30_short`
            """
        

    def getData(self):
        query_job = self.client.query(self.query_t)
        transactions = query_job.result().to_dataframe().drop('date_', axis=1).groupby(['from_address', 'to_address']).sum().reset_index()
        print(transactions.head())
        print(transactions.columns)
        transactions.columns = ["from_address", "to_address", "interactions_num"]
        return transactions