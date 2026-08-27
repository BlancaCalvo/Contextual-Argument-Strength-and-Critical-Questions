
import re
import json
from tqdm import tqdm
from langchain_openai import ChatOpenAI
import os
import csv

def structure_output(whole_text):
    cqs_list = whole_text.split('\n')
    final = []
    valid = []
    not_valid = []
    for cq in cqs_list:
        if re.match('.*\\?(\\")?( )?(\\([a-zA-Z0-9\\.\'\\-,\\? ]*\\))?([a-zA-Z \\.,\\"\']*)?(\\")?$', cq):
            valid.append(cq)
        else:
            not_valid.append(cq)

    still_not_valid = []
    for text in not_valid:
        new_cqs = re.split("\\?\"", text+'end')
        if len(new_cqs) > 1:
            for cq in new_cqs[:-1]:
                valid.append(cq+'?\\"')
        else:
            still_not_valid.append(text)

    for i, cq in enumerate(valid):
        occurrence = re.search(r'[A-Z]', cq)
        if occurrence:
            final.append(cq[occurrence.start():])
        else:
            continue

    output = []
    for i in range(len(final)):
        output.append({'id':i, 'cq':final[i]})
    return output


def main():
    model_name = "gpt-4o-2024-08-06"
    api_key = os.environ.get('OPENAI_API_KEY')


    INPUT_CSV = "data/recursive_cqs_generation/1_recursive_cqs_generation - claude-sonnet-4-6.csv"
    OUTPUT_CSV = "data/recursive_cqs_generation/2_"+model_name+".csv"

    prompt = """Suggest 5 critical questions that should be raised before accepting the argument in this text:
                
                Text: {context} "{argument}"
                
                Give one question per line. Make the questions simple, and do not give any explanation reagrding why the question is relevant."""

    llm = ChatOpenAI(model=model_name, api_key=api_key) #gpt-4o-mini o4-mini-2025-04-16

    with open(INPUT_CSV, "r", encoding="utf-8") as infile, \
     open(OUTPUT_CSV, "w", encoding="utf-8", newline="") as outfile:

        writer = csv.writer(outfile)
        infile_read = list(csv.reader(infile, delimiter=','))
        writer.writerow(infile_read[0])

        for line in infile_read[1:]:
            response = llm.invoke(prompt.format(**{'context':line[5].strip(),
                                                'argument': line[6].strip()}))
            answer = response.content

            line.append(answer)

            writer.writerow(line)
            #exit()


if __name__ == "__main__":
        main()