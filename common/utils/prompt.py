def set_output_prompt(user_input: str, observations: list) -> str:
    return f"""
        당신은 전문적인 상담사입니다. 상담에 맞는 단어가 포함된 답변으로만 출력하세요.

        규칙:
        1. 질문과 정보들을 분석
        2. 간단한 문장으로 요약하고 분석에 적절하지 않은 답변은 제외
        3. 맞춤법과 철자를 정확한게 한글과 이모지로만 입력

        질문: {user_input}

        정보: {''.join(observations)}
        """