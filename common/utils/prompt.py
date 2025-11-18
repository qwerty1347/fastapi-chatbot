def set_output_prompt(user_input: str, observations: str) -> str:
    return f"""
        정보를 활용하여 질문에 가장 적절한 답변으로 규칙에 맞게 출력할 것

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
        질문이 단순 인간의 감정 표현(인사, 고마움, 슬픔, 위로, 잡담 등) 또는 일상적인 대화인지 판별할 것
        질문이 정보 요청이나 특정 사안에 대한 사실 확인이면 no 만 출력할 것
        질문이 단순 일상 대화라면 yes 만 출력할 것

        규칙:
        - 출력은 yes 또는 no 단 한 단어만 사용할 것
        - 어떠한 설명도 추가하지 말 것

        질문: {user_input}
        """


def set_chitchat_prompt(user_input: str) -> str:
    return f"""
        질문에 가장 적절한 답변을 자연스러운 한국어 대화로 출력하고 절대 영어를 사용하지 말 것
        적절한 이모지를 넣어 출력할 것

        예시:
        안녕하세요! 😊 오늘 기분은 어떠세요?

        질문: {user_input}
        """