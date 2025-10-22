def set_output_prompt(user_input: str, observations: str) -> str:
    return f"""
        아래 질문에 알맞게 적절한 답변으로만 아래 규칙에 맞게 간략하게 출력할 것

        규칙:
        질문과 정보들을 분석하고 정확한 정보를 간단한 문장으로 요약
        맞춤법과 철자를 정확히 지키고 한글과 이모지로만 입력
        줄바꿈은 문단 단위에서만 추가

        질문: {user_input}

        정보: {observations}

        """


def is_chitchat_prompt(user_input: str) -> str:
    return f"""
        아래 질문이 단순 인사, 고마움, 슬픔 등 인간의 감정을 표현, 잡담 등 일상적인 대화인지 판별할 것
        해당하면 yes, 아니면 no 로 출력

        질문: {user_input}

        """


def set_chitchat_prompt(user_input: str) -> str:
    return f"""
        아래 질문에 맞는 적절하게 출력하고 문장의 끝에는 상황에 맞는 적절한 이모지 또는 이모티콘을 넣어줘

        질문: {user_input}
    """