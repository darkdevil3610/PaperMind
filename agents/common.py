from pathlib import Path

from utils.gemini_client import get_gemini_client


DEFAULT_MODEL = "gemini-3.5-flash"
DEFAULT_CHAR_LIMIT = 12000

ROOT_DIR = Path(__file__).resolve().parents[1]
SKILLS_DIR = ROOT_DIR / "skills"


def load_skill(filename):
    return (SKILLS_DIR / filename).read_text(encoding="utf-8").strip()


def trim_text(text, char_limit=DEFAULT_CHAR_LIMIT):
    text = text or ""
    if len(text) <= char_limit:
        return text
    head_len = max(1, int(char_limit * 0.7))
    tail_len = max(1, char_limit - head_len)
    head = text[:head_len]
    tail = text[-tail_len:]
    return f"{head}\n\n[... middle of paper omitted for length ...]\n\n{tail}"


def run_gemini(prompt, model_name=DEFAULT_MODEL):
    response = get_gemini_client().models.generate_content(
        model=model_name,
        contents=prompt,
    )
    return response.text or ""
