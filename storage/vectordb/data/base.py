from storage.vectordb.data.board.notice import notices
from storage.vectordb.data.dev.openapi import openapis


def get_vectordb_data():
    return {
        "notice": notices,
        "openapi": openapis,
    }
