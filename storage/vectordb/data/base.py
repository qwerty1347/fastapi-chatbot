from storage.vectordb.data.board.notice import notices


def get_vectordb_data():
    return {
        "notice": notices,
    }
