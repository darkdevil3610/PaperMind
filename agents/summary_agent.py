from agents.common import DEFAULT_CHAR_LIMIT, DEFAULT_MODEL, load_skill, run_gemini, trim_text


def run_summary_agent(paper_text, model_name=DEFAULT_MODEL, char_limit=DEFAULT_CHAR_LIMIT):
    prompt = f"""
{load_skill("summary_skill.md")}

Return the answer with clear Markdown headings and concise bullets.

Paper text:
{trim_text(paper_text, char_limit)}
"""

    return run_gemini(prompt, model_name)
