import csv
import json
import os
import sys
import re
import argparse
from tqdm import tqdm
from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage

# Try to get API key from environment
api_key = os.environ.get('OPENAI_API_KEY')

def load_data(file_path):
    """Loads CSV data using the csv module (no pandas)."""
    with open(file_path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        return list(reader)

def generate_prompt(situation, argument, question, critical_questions_raw):
    """Generates the prompt for the OpenAI model."""
    # Split critical questions by newline
    references = [q.strip() for q in critical_questions_raw.strip().split('\n') if q.strip()]
    
    listed_references = ''
    for i, ref in enumerate(references):
        # Remove leading numbers if they exist (e.g., "1. Question") to avoid double numbering
        clean_ref = re.sub(r'^\d+[\.\)]\s*', '', ref)
        listed_references += f"{i}. {clean_ref}\n"

    system_prompt = """You are an expert in argument-structure analysis.

Your task is to determine whether a new question matches one of the argumentative probe types present in a reference set.

Important rules:

- A MATCH requires a close structural twin in the reference set.
- The twin must probe the same argumentative dimension, not merely be about the same topic.
- If the new question introduces a new probing dimension, even if related to the context, classify it as DIFFERENT.
- The reference set defines the complete set of acceptable probing dimensions. Do not invent additional ones.
"""

    prompt = f"""CONTEXT:
{situation} "{argument}". Ask questions to evaluate the strength of the argument in this context.

REFERENCE QUESTIONS:
{listed_references}

NEW QUESTION:
{question}

TASK:

Step 1: Identify the probing dimension of each reference question.
Step 2: Identify the probing dimension of the new question.
Step 3: Determine whether the new question matches one of the reference probing dimensions.

If MATCH:
    - Specify which reference question number is the closest structural twin.
If DIFFERENT:
    - State "No structural twin found."

Return your final answer in JSON format:

{{
  "classification": "MATCH" or "DIFFERENT",
  "closest_reference_question": number or null,
  "confidence": 0-100,
  "reasoning": "brief explanation"
}}
"""

    messages = [
        SystemMessage(content=system_prompt),
        HumanMessage(content=prompt)
    ]
    return messages

def evaluate(input_path, output_path, ids_path=None):
    """Evaluates questions from the input CSV file and yields each evaluated entry."""
    print(f"Loading data from {input_path}...")
    data = load_data(input_path)

    target_instances = None
    if ids_path:
        if os.path.exists(ids_path):
            with open(ids_path, "r", encoding="utf-8") as f:
                ids_list = json.load(f)
                target_instances = { (str(d.get("session_id")), str(d.get("argument_id")), str(d.get("question_id"))) for d in ids_list }
            print(f"Loaded {len(target_instances)} target instances from {ids_path}")
        else:
            print(f"Error: {ids_path} not found.")
            return

    json_path = "/iratxo0/zerbitzuak/reflex-blanca/app/experiment_app/data/arguments_with_answers.json"
    print(f"Loading critical questions from {json_path}...")
    with open(json_path, "r", encoding="utf-8") as f:
        args_with_answers = json.load(f)
        
    cq_mapping = {}
    for item in args_with_answers:
        if "id" in item and "critical questions" in item:
            cq_mapping[str(item["id"])] = "\n".join(item["critical questions"])
    
    processed_ids = set()
    if os.path.exists(output_path):
        print(f"Output file {output_path} exists. Reading existing results...")
        try:
            with open(output_path, "r", encoding="utf-8") as f:
                for line in f:
                    if line.strip():
                        try:
                            obj = json.loads(line)
                            q_id = str(obj.get("metadata", {}).get("question_id", ""))
                            a_id = str(obj.get("metadata", {}).get("argument_id", ""))
                            s_id = str(obj.get("metadata", {}).get("session_id", ""))
                            if q_id:
                                processed_ids.add(f"{s_id}_{a_id}_{q_id}")
                        except:
                            pass
        except Exception as e:
            print(f"Warning: Could not read existing results: {e}")

    model_name = "gpt-5.4"
    print(f"Running evaluation with {model_name}...")
    print(f"Already processed: {len(processed_ids)} questions.")
    llm = ChatOpenAI(model=model_name, api_key=api_key)
    
    for row in tqdm(data):
        session_id = str(row.get("session_id", "unknown"))
        question_id = str(row.get("question_id", "unknown"))
        argument_id = str(row.get("argument_id", "unknown"))
        unique_id = f"{session_id}_{argument_id}_{question_id}"
        
        if target_instances is not None:
            if (session_id, argument_id, question_id) not in target_instances:
                continue

        if unique_id in processed_ids:
            continue

        situation = row.get("situation", "")
        argument = row.get("argument", "")
        question = row.get("question", "")
        answer = row.get("answer", "")
        
        if argument_id in cq_mapping:
            critical_questions_raw = cq_mapping[argument_id]
        else:
            critical_questions_raw = row.get("critical_questions", "")
        
        entry = {
            "context": {
                "situation": situation,
                "argument": argument,
                "question": question,
                "answer": answer,
                "critical_questions": critical_questions_raw
            },
            "metadata": {
                "question_id": question_id,
                "argument_id": argument_id,
                "session_id": session_id,
                "experimental_group": row.get("experimental_group", "")
            },
            "evaluation": {}
        }

        try:
            messages = generate_prompt(situation, argument, question, critical_questions_raw)
            response = llm.invoke(messages)
            
            content = response.content.strip()
            if content.startswith("```json"):
                content = content[7:-3].strip()
            elif content.startswith("```"):
                content = content[3:-3].strip()
            
            result = json.loads(content)
            entry["evaluation"]["gpt-5"] = result
            
        except Exception as e:
            print(f"Error processing question {question_id}: {e}")
            entry["evaluation"]["gpt-5"] = {"error": str(e)}

        yield entry

def main():
    parser = argparse.ArgumentParser(description="Evaluate pilot questions using OpenAI")
    parser.add_argument("--input", help="Path to the input CSV file with the questions (obtained with extract_questions.py)")
    parser.add_argument("--output", help="Path to the output JSONL file")
    parser.add_argument("--ids", nargs="?", default=None, help="Path to the target IDs JSON file (optional)")
    args = parser.parse_args()

    with open(args.output, "a", encoding="utf-8") as f:
        for entry in evaluate(args.input, args.output, args.ids):
            f.write(json.dumps(entry, ensure_ascii=False) + "\n")
            f.flush()

if __name__ == "__main__":
    main()

