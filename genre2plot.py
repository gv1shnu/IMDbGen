import pickle

hm_pickle = "db/hashmap.pickle"
try:
    with open(hm_pickle, "rb") as file:
        hashmap = pickle.load(file)
except FileNotFoundError:
    with open(hm_pickle, "wb") as file:
        pickle.dump({}, file)