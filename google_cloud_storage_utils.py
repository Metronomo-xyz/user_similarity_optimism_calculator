from google.cloud import storage
import pandas as pd
from typing import List


def get_bucket(token_json_path, bucket_name) -> storage.Bucket:
    """
    Get bucket with given name and token json file

    Parameters
    ----------
    token_json_path : str
        path to token json file
    bucket_name
        name of bucket
    """
    storage_client = storage.Client.from_service_account_json(token_json_path)
    bucket = storage_client.get_bucket(bucket_name)
    return bucket

def get_blob_list(storage_client, bucket_obj) -> List[str]:
    """
    Parameters
    ----------
    storage_client : storage.Client
        storage client to use to connect to bucket
    bucket_obj : storage.Bucket
        bucket to return list of blobs
    """

    def get_blob_name(blob):
        return blob.name
    return list(map(get_blob_name, list(storage_client.list_blobs(bucket_obj))))

def write_dataframe_to_blob(data_frame, bucket, blob_name) -> None:
    """
    Parameters
    ----------
    data_frame : pandas.DataFrame
        data frame to write in bucket
    bucket : storage.Bucket
        bucket to write dataframe to
    blob_name : str
        blob to write dataframe to
    """
    if (bucket.blob(blob_name).exists()):
        bucket.blob(blob_name).delete()
    bucket.blob(blob_name).upload_from_string(data_frame.to_csv(), 'text/csv')

def filter_blobs_by_path(blob_list, path) -> List[str]:
    """
    Parameters
    ----------
    blob_list : list[str]
        list of blobs to filter
    path : str
        path to search for in blobs' names
    """

    return list(filter(lambda b: path in b, blob_list))

def get_dataframe_from_blob(bucket, blob_name, token_json_path, fields=None) -> pd.DataFrame:
    """
    Parameters
    ----------
    bucket : storage.Bucket
        bucket to load the data from
    blob_name : str
        name of blob to load the data from
    token_json_path : str
        path to token json file
    fields : list[str]
        list of fields to get from dataframe
    """

    if (fields):
        return pd.read_csv("gs://" + bucket.name + "/" + blob_name,
                           storage_options={"token": token_json_path})[fields]
    else:
        return pd.read_csv("gs://" + bucket.name + "/" + blob_name,
                           storage_options={"token": token_json_path})

# TODO: somehow make this method more general
def filter_blobs_by_dates(blob_list, dates_arr) -> List[str]:
    """
    Parameters
    ----------
    blob_list : list[str]
        list of blobs to filter

    dates_arr : list[datetime.date]
        list of dates to leave the data only for given dates
    """

    def dateToStr(d):
        return d.strftime("%Y-%m-%d")

    dates = list(map(dateToStr, dates_arr))
    if ("action_receipt_actions" in blob_list[0]):
        return list(filter(lambda b: b.split("_")[3].split("/")[1] in dates, blob_list))
    if ("transactions" in blob_list[0]):
        return list(filter(lambda b: b.split("_")[1].split("/")[2] in dates, blob_list))
    else:
        raise ValueError("Not valid TX or Actions paths. Please provide correct paths list")

