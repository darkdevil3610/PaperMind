from agents.common import DEFAULT_MODEL, load_skill, run_gemini


def run_safety_agent(summary, methodology, evaluation, future_work, claims="", model_name=DEFAULT_MODEL):
    prompt = f"""
You are the Safety Review Agent.

{load_skill("safety_skill.md")}

Return:
1. Safety status: Safe / Needs Review
2. Issues found
3. Suggested corrections
4. Final safety note

Generated analysis:

SUMMARY:
{summary}

METHODOLOGY:
{methodology}

EVALUATION:
{evaluation}

FUTURE WORK:
{future_work}

CLAIMS AND EVIDENCE:
{claims}
"""

    return run_gemini(prompt, model_name)
