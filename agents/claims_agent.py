from agents.common import DEFAULT_CHAR_LIMIT, DEFAULT_MODEL, load_skill, run_gemini, trim_text


def run_claims_agent(paper_text, model_name=DEFAULT_MODEL, char_limit=DEFAULT_CHAR_LIMIT):
    prompt = f"""
You are the Claims and Evidence Agent.

{load_skill("claims_skill.md")}

Return 5 to 8 claims. Use the support levels: Strong / Moderate / Weak / Not clear.

Do not invent citations, numbers, datasets, or results.

Paper text:
{trim_text(paper_text, char_limit)}
"""

    return run_gemini(prompt, model_name)
