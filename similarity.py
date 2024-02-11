import scipy.sparse as ss
import numpy as np
import math

def calculateSimilarity(data, removeWalletsPercentile=None, removeContractsPercentile=None, removeContracts=None):# -> ss.coo_matrix:
    if (removeWalletsPercentile):
        interactions_num_perc = np.percentile(data.interactions_num, removeWalletsPercentile)
        print("remove from interactions percentile : " + str(interactions_num_perc))

    if (removeContractsPercentile):
        to_interactions_count = data[["from_address", "to_address"]].groupby("to_address")\
            .count().sort_values(by="from_address", ascending=False)
        to_interactions_perc = np.percentile(to_interactions_count.from_address, removeContractsPercentile)
        leaveContracts = set(to_interactions_count[to_interactions_count.from_address <= to_interactions_perc]\
                             .reset_index()["to_address"].tolist())
        print(to_interactions_count.head(10))
        print("remove to interactions percentile : " + str(to_interactions_perc))

    if (removeWalletsPercentile):
        if(removeContractsPercentile):
            if(removeContracts):
                print("remove contracts : " + str(removeContracts))
                leaveContracts = leaveContracts - removeContracts
                data = data[(data.interactions_num <= interactions_num_perc) & (data.to_address.isin(leaveContracts))]
                data = data[data.from_address != data.to_address]
            else:
                data = data[(data.interactions_num <= interactions_num_perc) & (data.to_address.isin(leaveContracts))]
                data = data[data.from_address != data.to_address]
        else:
            if (removeContracts):
                print("remove contracts : " + str(removeContracts))
                data = data[(data.interactions_num <= interactions_num_perc) & (~data.to_address.isin(removeContracts))]
                data = data[data.from_address != data.to_address]
            else:
                data = data[data.interactions_num <= interactions_num_perc]
                data = data[data.from_address != data.to_address]
    else:
        if (removeContractsPercentile):
            if (removeContracts):
                print("remove contracts : " + str(removeContracts))
                leaveContracts = leaveContracts - removeContracts
                data = data[data.to_address.isin(leaveContracts)]
                data = data[data.from_address != data.to_address]
            else:
                data = data[data.to_address.isin(leaveContracts)]
                data = data[data.from_address != data.to_address]
        else:
            if (removeContracts):
                print("remove contracts : " + str(removeContracts))
                data = data[~data.to_address.isin(removeContracts)]
                data = data[data.from_address != data.to_address]
            else:
                data = data[data.from_address != data.to_address]

    wallets = data["from_address"].drop_duplicates().reset_index().drop("index", axis=1).reset_index()
    print("wallets num : " + str(len(wallets)))

    to_contracts = data["to_address"].drop_duplicates().reset_index().drop("index", axis=1).reset_index()
    print("to_contracts num : " + str(len(to_contracts)))

    data = data.set_index("from_address") \
        .join(
        wallets.set_index("from_address"),
        how="left") \
        .reset_index(drop=True) \
        .set_index("to_address") \
        .join(
        to_contracts.set_index("to_address"),
        how="left", lsuffix="_from", rsuffix="_to") \
        .reset_index(drop=True) \
        .drop("interactions_num", axis=1) \
        .drop_duplicates()

    row = np.array(data["index_from"])
    col = np.array(data["index_to"])
    d = np.array(np.ones(len(data)))
    print("creating matrices")
    m1 = ss.coo_matrix((d, (row, col))).astype(np.uintc).tocsr()
    m2 = m1.transpose()

    print("multiplying matrices")
    common_contracts = m1.dot(m2).tocoo()

    a = data.groupby("index_from").count().apply(lambda x: math.sqrt(x), axis=1).to_dict()

    wallets_index = wallets.set_index("index").to_dict()["from_address"]
    print("number of entries : " + str(len(common_contracts.data)))
    print("calculating similarity")

    row = [wallets_index[idx] for idx in common_contracts.row]
    print("replaced row indexes with wallets")
    col = [wallets_index[idx] for idx in common_contracts.col]
    print("replaced column indexes with wallets")
    data_similarity = [(d/(a[c]*a[r])) for r,c,d in zip(common_contracts.row, common_contracts.col, common_contracts.data)]
    print("calculated similarity")

    return list(zip(row, col, data_similarity))