from storage.vectordb.data.notice import notices


def get_vectordb_data():
    return {
        "notice": notices,
    }
