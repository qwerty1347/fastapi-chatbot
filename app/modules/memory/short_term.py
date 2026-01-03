from collections import deque


class ShortTermMemory:
    def __init__(self, max_messages=10):
        self.buffer = deque(maxlen=max_messages)


    def build_format_history(self):
        return "\n".join([f"{item['role']}: {item['content']}" for item in self.buffer])