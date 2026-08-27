import json
import csv
import re
from tqdm import tqdm
from langchain_openai import ChatOpenAI
import os

api_key = os.environ.get('OPENAI_API_KEY')

INPUT_CSV = "data/recursive_cqs_generation/5_final.csv"
CORRECT_INPUT = "data/recursive_cqs_generation/no_context_rating_names_change.csv"
OUTPUT_CSV = "data/recursive_cqs_generation/6_final_with_names.csv"

prompt = """
Rewrite the questions so that they use the names of the characters in the story. Change the person, but not the content or format. For example, if the situation is about my friend Alex and the argument comes from someone called Mike, the rewriting could be: "Does Alex like this?" or "How does Mike know this information?". Do not write any new question nor change the content to any of them. Do not reformat them either. Not all questions need character names, as some of them are generic about the situation, only use the character names when needed. 

Story: {context} "{argument}"

Questions: {questions}

"""


with open(INPUT_CSV, "r", encoding="utf-8") as infile, \
    open(CORRECT_INPUT, "r", encoding="utf-8") as corrections, \
     open(OUTPUT_CSV, "w", encoding="utf-8", newline="") as outfile:

    writer = csv.writer(outfile)
    infile_read = list(csv.reader(infile, delimiter=','))
    corrections_read = list(csv.reader(corrections, delimiter=','))
    writer.writerow(infile_read[0])

    llm = ChatOpenAI(model="gpt-4o-mini", api_key=api_key)

    for line in infile_read[1:]:
        correct = None
        for cor in corrections_read:
            if line[0]+line[2]+line[1] == cor[0]+cor[2]+cor[1]:
                correct = cor

        if correct:
        
            response = llm.invoke(prompt.format(**{'context':correct[5],
                                                    'argument': correct[6],
                                                    'questions': line[7]}))
            answer = response.content

            line[5]=correct[5]
            line[6]=correct[6]
            line[7]=answer
            line.append(line[0]+line[2]+line[1])
            writer.writerow(line)
        else:
            print('something went wrong', line[0]+line[2]+line[1])

        
        #exit()

