import anthropic
import json
import os
import csv
from tqdm import tqdm
import random

client = anthropic.Anthropic(api_key=os.environ.get('ANTHROPIC_API_KEY'))

RESPONSE_TYPE_PROMPTS = {
    "irrefutable": "Generate a fact that makes the argument practically irrefutable in this context. The fact should strongly support the key premises of the argument, leaving almost no room for doubt.",
    "favorable": "Generate a fact that supports the argument in this context. The fact should back up one of the argument's premises, but not so strongly that it removes all doubt.",
    "undermining": "Generate a fact that weakens the argument in this context. The fact should cast doubt on one of the argument's premises, but not completely destroy the argument.",
    "neutral": "Generate a fact that is relevant to the situation but does not affect the strength of the argument in either direction.",
    "invalidating": "Generate a fact that directly contradicts or invalidates a key premise of the argument in this context, making the argument very hard to sustain."
}

LABEL_DISTRIBUTIONS = {
    "strong": {
        "irrefutable": (2, 3),
        "others": ["favorable", "undermining", "neutral"]
    },
    "reasonable": {
        "favorable": 0.7,
        "undermining": 0.3,
        "neutral": "possible"
    },
    "weak": {
        "favorable": 0.3,
        "undermining": 0.7,
        "neutral": "possible"
    },
    "not supported": {
        "invalidating": (2, 3),
        "others": ["favorable", "undermining", "neutral"]
    }
}

def get_response_type_sequence(label: str, num_cqs: int) -> list[str]:
    """
    Given a label and number of CQs, returns the ordered list of response types
    to assign to each CQ.
    """
    import random

    if label == "strong":
        n_irrefutable = 2 if num_cqs <= 5 else 3
        n_irrefutable = min(n_irrefutable, num_cqs)
        remaining = num_cqs - n_irrefutable
        others = random.choices(["favorable",  "neutral"], k=remaining) # "undermining",
        sequence = ["irrefutable"] * n_irrefutable + others

    elif label == "not supported":
        n_invalidating = 2 if num_cqs <= 5 else 3
        n_invalidating = min(n_invalidating, num_cqs)
        remaining = num_cqs - n_invalidating
        others = random.choices(["undermining", "neutral"], k=remaining) # "favorable", 
        sequence = ["invalidating"] * n_invalidating + others

    elif label == "reasonable":
        n_favorable = round(num_cqs * 0.7)
        n_undermining = num_cqs - n_favorable
        sequence = ["favorable"] * n_favorable + ["neutral"] * n_undermining

    elif label == "weak":
        n_undermining = round(num_cqs * 0.7)
        n_favorable = num_cqs - n_undermining
        sequence = ["undermining"] * n_undermining + ["neutral"] * n_favorable

    else:
        raise ValueError(f"Unknown label: {label}")

    random.shuffle(sequence)
    return sequence


def generate_cq_response(
    situation: str,
    argument: str,
    cq: str,
    response_type: str,
    previous_responses: list[dict],
    label: str
) -> str:
    """
    Generates a single factual response to a CQ, given its response type
    and the previously generated responses for coherence.
    """

    previous_context = ""
    if previous_responses:
        previous_context = (
            "The following facts have already been established for this situation. "
            "They form part of the same context you are contributing to. "
            "Your response must be fully consistent with all of them:\n\n"
        )
        for prev in previous_responses:
            previous_context += f"- {prev['response']}\n"
        previous_context += "\n"

    prompt = f"""You are an expert in argumentation theory and context design for behavioral experiments.

Situation: {situation}
Argument: "{argument}"

Critical question: "{cq}"

{previous_context}
Your task: {RESPONSE_TYPE_PROMPTS[response_type]}

Rules:
1. Write one or two short, plain factual sentences. No literary language.
2. The fact must be directly relevant to the critical question.
3. Do not mention the argument label or explain why you are writing this fact.
4. COHERENCE IS MANDATORY: Before writing your response, check every established fact 
   above. Your response must not contradict any of them, even indirectly or implicitly. 
   For example, if a previous fact states that a character lives alone, do not write 
   anything that implies they live with others. If a previous fact establishes a 
   character's profession, do not write anything inconsistent with that profession.
5. Do not introduce proper names not mentioned in the situation. Use relational terms 
   (e.g. "a colleague", "a relative").
6. Do not use acronyms without defining them.
7. Write as a factual statement about the situation, not as a direct answer 
   to the question. However, the fact you write must address the specific 
   subject of the critical question. Do not write facts that are only 
   tangentially related to the question.
"""

    response = client.messages.create(
        model="claude-opus-4-5",
        max_tokens=200,
        messages=[{"role": "user", "content": prompt}]
    )

    return response.content[0].text.strip()


def generate_neutral_background(
    situation: str,
    argument: str,
    established_facts: list[dict]
) -> str:
    """
    Generates a short neutral background paragraph to complete the context.
    This should add color to the situation without containing information
    relevant to evaluating the argument.
    """

    facts_summary = "\n".join([f"- {f['cq']}: {f['response']}" for f in established_facts])

    prompt = f"""You are an expert in context design for behavioral experiments.

Situation: {situation}
Argument: "{argument}"

Facts already established in this context:
{facts_summary}

Your task: Write a short paragraph of neutral background information about the situation and characters. This paragraph should:
- Add realism and color to the situation
- Explain the main details of the situation someone could wonder about
- Be consistent with the established facts
- Contain NO information that could help evaluate the argument
- Use plain, direct language
- Not introduce proper names not present in the situation
- Maximum 300 words
"""

    response = client.messages.create(
        model="claude-opus-4-5",
        max_tokens=400,
        messages=[{"role": "user", "content": prompt}]
    )

    return response.content[0].text.strip()


def generate_full_context(
    situation: str,
    argument: str,
    label: str,
    cqs: list[str]
) -> dict:
    """
    Main function. Generates the full context for an argument by:
    1. Assigning a response type to each CQ
    2. Generating each CQ response sequentially
    3. Appending a neutral background paragraph
    
    Returns a dict with the full context and the breakdown by CQ.
    """

    sequence = get_response_type_sequence(label, len(cqs))
    
    previous_responses = []
    cq_responses = []

    for cq, response_type in zip(cqs, sequence):
        response = generate_cq_response(
            situation=situation,
            argument=argument,
            cq=cq,
            response_type=response_type,
            previous_responses=previous_responses,
            label=label
        )

        entry = {
            "cq": cq,
            "response_type": response_type,
            "response": response
        }

        cq_responses.append(entry)
        previous_responses.append(entry)

    background = generate_neutral_background(
        situation=situation,
        argument=argument,
        established_facts=cq_responses
    )

    full_context = "\n\n".join([r["response"] for r in cq_responses]) + "\n\n" + background

    return {
        "full_context": full_context,
        "breakdown": cq_responses,
        "background": background,
        "label": label,
        "sequence": sequence
    }

def main():
    INPUT_CSV = "data/recursive_cqs_generation/6_final_with_names.csv"
    OUTPUT_CSV = "data/context/structured_context.csv"
    with open(INPUT_CSV, "r", encoding="utf-8") as infile, \
         open(OUTPUT_CSV, "w", encoding="utf-8", newline="") as outfile:

        writer = csv.writer(outfile)
        infile_read = list(csv.reader(infile, delimiter=','))
        writer.writerow(infile_read[0])

        labels = ['not supported'] * 9 + ['weak'] * 9 + ['reasonable'] * 9 + ['strong'] * 9
        random.shuffle(labels)

        for i, line in enumerate(tqdm(infile_read[1:])):
            #if line[-1] != "5231":
            #    continue
            output = generate_full_context(
                situation=line[5].strip(),
                argument=line[6].strip(),
                label=labels[i],
                cqs=line[7].strip().split("\n")
            )
            line.extend([output["full_context"], output["breakdown"], output["background"], output["label"], output["sequence"]])
            writer.writerow(line)


if __name__ == "__main__":
    main()