import datetime
import os
import sys
from dotenv import load_dotenv
from user_similarity_optimism_calculator import events_data_connectors as dc
from user_similarity_optimism_calculator import similarity
from user_similarity_optimism_calculator import db_writers
import getopt

def check_type_conversion(value_, type_):
    if not value_:
        raise ValueError("Expected something, that is convertible to type " +
              str(type_) + ", but None was provided")

    try:
        return type_(value_)
    except ValueError as e:
        print("Value error : expected simething, that is convertible to type " +
              str(type_) + ", but " + str(value_) + " was provided")

if __name__ == '__main__':
    load_dotenv("user_similarity_optimism_calculator/static_config.env")
    load_dotenv()

    # reading environmental variables
    with_public_data = (os.getenv("USE_PUBLIC_DATA") == "True")
    try:
        start_date = datetime.datetime.strptime(os.getenv("START_DATE"), "%d%m%Y")
    except TypeError as e:
        print(e)
        print("Environmental variable START_DATE is not set")
        sys.exit(1)
    except ValueError as e:
        print(e)
        print("Environmental variable START_DATE is" + os.getenv("START_DATE"))
        sys.exit(1)

    dates_range = check_type_conversion(os.getenv("DATES_RANGE"), int)

    try:
        remove_contracts = set(os.getenv("REMOVE_CONTRACTS").split(","))
    except Exception as e:
        print(e)
        print("Environmental variable REMOVE_CONTRACTS is not set")
        sys.exit(1)

    remove_wallets_percentile = check_type_conversion(os.getenv("REMOVE_WALLETS_PERCENTILE"), float)
    remove_contracts_percentile = check_type_conversion(os.getenv("REMOVE_CONTRACTS_PERCENTILE"), float)
    project_name = check_type_conversion(os.getenv("METRONOMO_PUBLIC_DATA_PROJECT"), str)
    dataset = check_type_conversion(os.getenv("METRONOMO_PUBLIC_DATA_DATASET"), str)
 
    if os.getenv("MONGO_HOST"):
        mongo_host = check_type_conversion(os.getenv("MONGO_HOST"), str)
    else:
        mongo_host = '127.0.0.1'

    if os.getenv("MONGO_PORT"):
        mongo_port = check_type_conversion(os.getenv("MONGO_PORT"), int)
    else:
        mongo_port = 27017

    mongo_database = check_type_conversion(os.getenv("MONGO_DATABASE"), str)
    mongo_collection = check_type_conversion(os.getenv("MONGO_COLLECTION"), str)

    token_json_path = check_type_conversion(os.getenv("METRONOMO_BQ_TOKEN_JSON_PATH"), str)

    # generating dates rane
    dates = [start_date - datetime.timedelta(days=x) for x in range(dates_range)]
    print("Dates : " +  ",".join([str(d) for d in dates]))

    # creating connector to public Optimism data storage
    bq_connector = dc.MetronomoOptimismTXBigQueryConnector(dates, project=project_name, dataset=dataset, token_json_path=token_json_path)

    # retrieving data
    data = bq_connector.getData()
    print("Data loaded")

    # calculating similatiry
    zipped_similarity = similarity.calculateSimilarity(data, remove_wallets_percentile, remove_contracts_percentile, remove_contracts)

    print(str(sys.getsizeof(zipped_similarity)/1024/1024/1024))
    print("creating lines")
    lines = [",".join([x[0], x[1], str(x[2])]) for x in zipped_similarity]
    print("writing file")

    with open('somefile2.txt', 'w') as fp:
        for line in lines:
            fp.write("%s\n" % line)
    print("finished writing file")

#    writing similarity to MongoDB
    print("writing to mongo")

    mongo_writer = db_writers.MongoWriter(mongo_host, mongo_port)
    mongo_writer.writeSimilarityToCollection(zipped_similarity, mongo_database, mongo_collection)

    print("finished writing to mongo")


    sys.exit()

