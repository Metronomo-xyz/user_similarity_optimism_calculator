from abc import ABC, abstractmethod
import pandas as pd
from dotenv import load_dotenv
from google.cloud import bigquery
from google.oauth2 import service_account
from user_similarity_optimism_calculator import google_cloud_storage_utils as csu
from google.cloud import storage


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
        self.client = bigquery.Client(credentials= self.credentials,project=project)

        self.query_t = """
            SELECT * 
            FROM `web3advertisement.optimism_data.transactions_full_30_short`
            """
        

    def getData(self):
        query_job = self.client.query(self.query_t)
        transactions = query_job.result().to_dataframe().drop('date_', axis=1).groupby(['from_address', 'to_address']).sum().reset_index()
        transactions.columns = ["from_address", "to_address", "interactions_num"]
        return transactions
    

class MetronomoTXCloudStorageConnector(DataConnector):
    # This class implements DataConnector class
    # and incapsulates the logic to retrieve TX data from
    # Metronomno.xyz Google Cloud Storage

    # Current implementation will NOT be useful for anyone who wants to use power_users tool
    # However if you use data from your own Google Cloud Storage it is possible to adjust the code to your needs

    # The main source of data below was NEAR Indexer for Explorer PostgresSQL database
    # https://github.com/near/near-indexer-for-explorer
    # We get transactions table once a day for previous day in a hourly batches.
    # Then we combine hourly batches into one daily batch

    # MetronomoTXCloudStorageConnector stores some data structure for Metronomno.xyz Google Cloud Storage data
    # for using in Power Users module

    def __init__(self,
                 dates,
                 bucket_name,
                 blob_name,
                 with_public_data = False,
                 token_json_path=None):
        """
        Parameters
        ----------
        dates: list[datetime.Date]
            dates range to retrieve the data. Should be iterable of datetime.date type
        run_local: str
            flag to run code locally (priority higher than token_json_path). In case of local running path for local toke_json file is used
        bucket_name: str
            name of the bucket to get data from. Either provided or got from .env file, variable MetronomoTXCloudStorageConnector_DEFAULT_BUCKET_NAME
        token_json_path: str
            path to token json file. Either provided or got from .env file, variable MetronomoTXCloudStorageConnector_TOKEN_JSON_PATH
        network:
            network to get data from. Currently, possible only "mainnet" data
        granularity:
            data granularity to retrive. Currently possible only "daily" data
        """

        load_dotenv("user_similarity_near_calculator/static_config.env")

        self.with_public_data = with_public_data
        print("Using public data : " + str(self.with_public_data))

        if ((with_public_data == False) & (token_json_path is None)):
            raise ValueError("None of --public_data or --token_json_path is provided. Please use either public data or your own data with provided token json path.")


        if (self.with_public_data):
            self.token_json_path = None
            self.storage_client = storage.Client().create_anonymous_client()

        else:
            self.token_json_path = token_json_path
            self.storage_client = storage.Client.from_service_account_json(self.token_json_path)

        self.bucket_name = bucket_name
        self.blob_name = blob_name
        self.bucket = self.storage_client.bucket(self.bucket_name)
        self.dates = dates

    def __str__(self):
        return "CloudStorageConnectror object : " + "\n" + \
               "bucket_name : " + str(self.bucket_name) + "\n" + \
               "token_json_path : " + str(self.token_json_path) + "\n" + \
               "storage_client : " + str(self.storage_client) + "\n" + \
               "bucket : " + str(self.bucket) + "\n" + \
               "network : " + str(self.network) + "\n" + \
               "dates : " + str(self.dates) + "\n" + \
               "granularity : " + str(self.granularity)

    def getData(self):
        tx_df = pd.DataFrame()
        print("reading tx blobs:")
        tx_b = self.blob_name
        print(tx_b)
        tx_df = csu.get_dataframe_from_blob(
            self.bucket,
            tx_b,
            self.token_json_path
        )
        tx_df = tx_df.drop('date_', axis=1).groupby(['from_address', 'to_address']).sum().reset_index()
        tx_df.columns = ["from_address", "to_address", "interactions_num"]

        return tx_df