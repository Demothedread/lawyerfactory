from ..bot_interface import Bot


class LegalEditorBot(Bot):
    async def process(self, text: str) -> str:
        # Placeholder for real review logic
        return f"Feedback for '{text}'"
