def set_output_prompt(user_input: str, observations: str) -> str:
    return f"""
        아래 질문에 알맞게 적절한 답변으로 아래 규칙에 맞게 출력할 것

        규칙:
        - 맞춤법과 철자를 정확히 지킬 것
        - 줄바꿈(\n)은 1번씩만 사용할 것
        - 내용을 요약하고 중요 내용만 간결하게 출력할 것
        - 부드러운 어조를 사용하고 문장의 끝에는 적절한 이모지를 줄바꿈(\n) 사용하지 않고 출력할 것

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
        아래 질문에 맞는 적절하게 출력하고 적절한 이모지를 넣어 자연스러운 대화로 출력할 것

        질문: {user_input}
        """