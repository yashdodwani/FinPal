"""
Honeypot Agent Prompts
----------------------

Contains prompt templates for:
- persona_prompt.txt: Human persona generation
- extraction_prompt.txt: Intelligence extraction
- strategy_prompt.txt: Engagement strategy selection
"""

from pathlib import Path

PROMPTS_DIR = Path(__file__).parent


def load_prompt(name: str) -> str:
    """Load a prompt template by name."""
    path = PROMPTS_DIR / f"{name}.txt"
    return path.read_text(encoding="utf-8")


def get_persona_prompt() -> str:
    return load_prompt("persona_prompt")


def get_extraction_prompt() -> str:
    return load_prompt("extraction_prompt")


def get_strategy_prompt() -> str:
    return load_prompt("strategy_prompt")
