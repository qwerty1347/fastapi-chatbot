def set_output_prompt(user_input: str, observations: str) -> str:
    return f"""
        아래 질문에 알맞게 적절한 답변으로만 아래 규칙에 맞게 4문단 이내로 출력할 것

        규칙:
        - 질문과 정보들을 분석하고 정확한 정보를 간단한 문장으로 요약
        - 맞춤법과 철자를 정확히 지켜줘
        - 가능하다면 문장의 끝에는 상황에 맞는 적절한 이모지를 넣어줘
        - 줄바꿈은 문단 단위에서만 추가할 것
        - 상황에 따라 표 등으로 깔끔하게 요약

        질문: {user_input}

        정보: {observations}
        """


def is_chitchat_prompt(user_input: str) -> str:
    return f"""
        아래 질문이 단순 인간의 감정 표현(인사, 고마움, 슬픔, 위로, 슬픔, 잡담 등) 일상적인 대화인지 판별할 것
        해당하면 yes, 아니면 no 로 출력

        질문: {user_input}
        """


def set_chitchat_prompt(user_input: str) -> str:
    return f"""
        아래 질문에 맞는 적절하게 출력하고 상황에 맞는 적절한 이모티콘을 넣어 자연스러운 대화로 출력할 것

        질문: {user_input}
        """