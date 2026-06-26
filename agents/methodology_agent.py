from agents.common import DEFAULT_CHAR_LIMIT, DEFAULT_MODEL, load_skill, run_gemini, trim_text


def run_methodology_agent(paper_text, model_name=DEFAULT_MODEL, char_limit=DEFAULT_CHAR_LIMIT):
    prompt = f"""
You are the Methodology Agent.

{load_skill("methodology_skill.md")}

Return a compact technical breakdown. If a detail is missing, say "Not clearly stated".

Paper text:
{trim_text(paper_text, char_limit)}
"""

    return run_gemini(prompt, model_name)
