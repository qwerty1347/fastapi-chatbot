class ToolConstants:
    WEB_SEARCH = "WEB_SEARCH"
    DB_SEARCH = "DB_SEARCH"

    descriptions = {
        DB_SEARCH: {
            "description": "도매꾹과 관련된 모든 정보 검색에 사용. 질문에 '도매꾹'이 포함되어 있다면 항상 DB_SEARCH 사용할 것",
        },
        WEB_SEARCH: {
            "description": "도매꾹을 제외한 일반 정보 검색에 사용할 것",
        }
    }