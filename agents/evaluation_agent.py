from agents.common import DEFAULT_CHAR_LIMIT, DEFAULT_MODEL, load_skill, run_gemini, trim_text


def run_evaluation_agent(paper_text, model_name=DEFAULT_MODEL, char_limit=DEFAULT_CHAR_LIMIT):
    prompt = f"""
You are the Evaluation Agent.

{load_skill("evaluation_skill.md")}

Focus on evidence quality, metric clarity, baseline strength, and limitations.
If the paper does not provide enough evidence, say so plainly.

Paper text:
{trim_text(paper_text, char_limit)}
"""

    return run_gemini(prompt, model_name)
