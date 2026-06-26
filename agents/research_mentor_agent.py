from agents.common import DEFAULT_CHAR_LIMIT, DEFAULT_MODEL, load_skill, run_gemini, trim_text


def run_research_mentor_agent(paper_text, model_name=DEFAULT_MODEL, char_limit=DEFAULT_CHAR_LIMIT):
    prompt = f"""
You are the Research Mentor Agent.

{load_skill("research_mentor_skill.md")}

Prioritize suggestions that are actionable for a student research project.

Paper text:
{trim_text(paper_text, char_limit)}
"""

    return run_gemini(prompt, model_name)
