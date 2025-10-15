def set_output_prompt(user_input: str, observations: str) -> str:
    return f"""
        아래 질문에 알맞게 적절한 답변으로만 아래 규칙에 맞게 간략하게 출력할 것

        규칙:
        질문과 정보들을 분석
        간단한 문장으로 요약하고 분석에 적절하지 않은 답변은 제외
        맞춤법과 철자를 정확한게 한글과 이모지로만 입력
        줄바꿈은 문단 단위에서만 추가 (파라미터에서는 추가하지 말것)

        질문: {user_input}

        정보: {observations}

        """


def is_chitchat_prompt(user_input: str) -> str:
    return f"""
        아래 질문이 단순 인사, 감정 표현, 잡담 등 일상 대화인지 판별할 것
        해당하면 yes, 아니면 no 로 출력

        질문: {user_input}

        """


def set_chitchat_prompt(user_input: str) -> str:
    return f"""
        아래 질문에 맞는 적절한 답변으로 출력할 것

        질문: {user_input}
    """