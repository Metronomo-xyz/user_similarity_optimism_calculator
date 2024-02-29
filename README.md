# user_similarity_optimism_calculator
Tool to calculate users similarity on Optimism blockchain

It's part of user_similarity_optimism functionality

![architecture](http://dl3.joxi.net/drive/2024/02/25/0016/0232/1081576/76/fcf7b0a8f8.jpg)

This module calculates users similarity based on transactions data and stores it in provided Google Cloud Storage blob.

After that, you can load this similarity data into user_similarity_optimism_app and request similarities from it.

Be aware, that calculation of similarity with popular smart contract will lead to $O(n^2)$ memory consumption. Therefore, highly recommended removing from analysis smart contract, which has very large number of users.

Also, it's reasonable from the gained information perspective: if some smart contract is used by almost every participant in the network, then there is no new and useful information that wallet interacted with this smart contract in terms of determining wallet behaviour and interests.

Module uses some data cleaning steps:
- removing smart contract, which has the largest number of users from the analysis. See `REMOVE_CONTRACTS_PERCENTILE` variable in `static_config.env` 
- removing some hardcoded list of smart-contract from analysis. See `REMOVE_CONRACTS` variable in `static_config.env`
- removing users with high number of interactions (mostly bots) from analysis. See `REMOVE_WALLETS_PERCENTILE` variable in `static_config.env`

Because of percentile cleaning usage, it is possible, that using data from shorter period will lead to increase in memory consumption.
It happens, because on a short period of time the most popular smart contracts are not so separated from other in terms of interactions number. Therefore, they are not cleaned from analysis by 99-th percentile cut.

## Prerequisites

### Hardware
#### Calculation server
The main bottleneck of current module is RAM, so at least 16GB of RAM needed. Memory consumption can be much higher ($O(n^2)$, where $n$ - is number of users of the most popular smart contract), if use more data or if not using popular smart contract interactions removal.

#### MongoDB Server
Any kind of preferred infrastructure for MongoDB server is possible. At least 10 GB of available disk space needed. Better to have 20GB or more of available disk space.

### Data source
Either you can use provided public transactions data or use your own data connector. 

To use public data user environmental variable `USE_PUBLIC_DATE` in `static_config.env`

To use your own data connector you have to implement DataConnector abstract class and provided some setting in config file (if needed). 

### Run MongoDB server

To store similarity module use MongoDB. 

You have to run MongoDB server and provide its host, port, database and collection to the module in `.env` file

## Running from Docker image
It's the easiest way to run the module

### 1. Create .env file

Copy `.env` file from `https://github.com/Metronomo-xyz/user_similarity_optimism_calculator`

Put it on your machine

Change values in .env file like described [below](#env)

### 2. Pull image from docker

```
sudo docker pull randromtk/user_similarity_optimism_calculator:dev
```

### 3. Run docker container

```
sudo docker run -it --env-file <path to .env file> <image tag>
```

- `<path to .env file>` - path to file, that you created [before](#1createenvfile)
- `<image tag>` - image tag. Might be obtained by running `sudo docker images` command, in our example is "randromtk/user_similarity_optimism_calculator:dev"

*To run locally (but this works only for Linux)*

```
sudo docker run -it --env-file <path to env file with local mongo host> --network="host" <image tag>
```

example:
```
sudo docker run -it --env-file new.env fd32c3c27e35
```

## Running from the source code

### 0. Clone repository

`git clone https://github.com/Metronomo-xyz/user_similarity_optimism_calculator.git`

### 1. Create virtual environment

It's recommended to use virtual environment while using module

If you don't have `venv` installed run (ex. for Ubuntu)
```
sudo apt-get install python3-venv
```
then create and activate virtual environment
```
python3 -m venv simcalc_optimism
source simcalc_optimism/bin/activate
```

### 2. Install requirements
Run
```
pip install -r user_similarity_optimism_calculator/requirements.txt
```

### 3. Set environmental variables

env-files:
- [.env](#env) - Need to take file from current repository as example, change it, and keep it in module directory (in the same directory as `__main__.py`)
- [static_config.env](#static_configenv) - better not to change

#### .env

Variables to access MongoDB server. You HAVE to set your own

```
- MONGO_HOST - host of mongodb server to write similarities data to
- MONGO_PORT - port of mongodb server  to write similarities data to
- MONGO_DATABASE  - mongo database name to write similarities data to
- MONGO_COLLECTION  - mongo collection name to write similarities data to
```

Dates choosing. You might use any START_DATE and DATE_RANGE as you want
```
- START_DATE - the last date of the dates period in `ddmmyyyy` format
- DATES_RANGE - number of days to take into power users calculation. For example, if start date is 12122022 and range 30 then dates will be since 13-11-2022 to 12-12-2022 inclusively
```
#### static_config.env
Better not to change them. But if you want to change - do it on your own risk.
```
 - USE_PUBLIC_DATA
 
# Flag to user publicly available Optimism blockchain data.
# If `True` data from Metronomo public bucket will be used
# If `False` - you have to write your own class to get the data from your own storage 

```

Config file with environment variables to get public Optimism data from Metronomo cloud storage. DO NOT CHANGE
```
- METRONOMO_PUBLIC_DATA_PROJECT
- METRONOMO_PUBLIC_DATA_BUCKET_NAME
- METRONOMO_PUBLIC_DATA_NETWORK
- METRONOMO_PUBLIC_DATA_GRANULARITY
```

Variables to configure data removal for similarity calculation.

Change with caution, preferably not change. Leaving popular contracts in calculation will lead to exponential memory and time complexity.

```
REMOVE_CONTRACTS - these contracts will be removed from similarity calculation (and from user vector representation)
REMOVE_CONTRACTS_PERCENTILE - Percentile of number overall contract interactions. Contracts in this boundary will be left in calculation. Contracts outside - will be removed
REMOVE_WALLETS_PERCENTILE - Percentile of number of overall user interactions. Wallets in this boundary will be left in calculation. Wallets outside - will be removed
```

### 4. Run the module

```python3 -m user_similarity_optimism_calculator```

Similarity result will be stored in MongoDB on host, port provided in .env, in database and collections provided in .env

