import json
import csv
import re
from tqdm import tqdm
from langchain_openai import ChatOpenAI
import os

api_key = os.environ.get('OPENAI_API_KEY')

INPUT_CSV = "data/6_chosen.csv"
OUTPUT_CSV = "data/7_chosen_contextual.csv"

prompt = """
Rewrite the following question by giving it a bit of context of who is asking them. Also introduce another person who going to give an argument. 

For example, for the question: "Should I switch from a night-and-weekend job to a daytime office job with lower starting pay?"
Generate something like: "A good friend of yours is wondering if they should switch from a night-and-weekend job to a daytime office job with lower starting pay? Another friend argues:"

Use generic characters which are not gendered. For instance: friend, parent, cousin, sibling, neighbour, colleague, etc. 

Here is the question: {question}

"""


with open(INPUT_CSV, "r", encoding="utf-8") as infile, \
     open(OUTPUT_CSV, "w", encoding="utf-8", newline="") as outfile:

    writer = csv.writer(outfile)
    infile_read = list(csv.reader(infile, delimiter=','))
    writer.writerow(infile_read[0])

    for line in infile_read[1:]:
        
        llm = ChatOpenAI(model="gpt-5", api_key=api_key) #gpt-4o-mini

        response = llm.invoke(prompt.format(**{'question':line[2]}))
        answer = response.content

        line[1] = answer

        writer.writerow(line)
        #exit()

