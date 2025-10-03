class ConversationMemory:
    def __init__(self, max_turns=5):
        self.history = []
        self.max_turns = max_turns

    def add(self, role: str, content: str):
        self.history.append({"role": role, "content": content})
        # Trim to moving window size
        if len(self.history) > self.max_turns * 2:
            self.history.pop(0)

    def get(self):
        return self.history
