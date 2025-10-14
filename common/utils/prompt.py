def set_output_prompt(user_input: str, observations: str) -> str:
    return f"""
        질문에 알맞게 적절한 답변으로만 간략하게 출력하세요.

        규칙:
        1. 질문과 정보들을 분석
        2. 간단한 문장으로 요약하고 분석에 적절하지 않은 답변은 제외
        3. 맞춤법과 철자를 정확한게 한글과 이모지로만 입력

        질문: {user_input}

        정보: {observations}

        """