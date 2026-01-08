import asyncio
import webbrowser
from pathlib import Path

from maestro.maestro import Maestro


def run_factory(topic: str) -> str:
    """Run the lawyer factory for the given topic and display the factory UI."""

    # Launch the factory floor interface in the user's browser.
    html_path = Path(__file__).with_name("factory.html").resolve()
    webbrowser.open(f"file://{html_path}")

    async def _run() -> str:
        maestro = Maestro()
        return await maestro.research_and_write(topic)

    return asyncio.run(_run())
