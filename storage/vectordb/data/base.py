from itertools import chain

from storage.vectordb.data.notice import notices


def get_vectordb_data():
    return list(chain(notices))