import json
import csv
import re

INPUT_CSV = "data/4_annotated.csv"
OUTPUT_CSV = "data/5_annotated_cqs_theory.csv"

with open('data/walton_plus.jsonl') as f:
    cqs = []
    for line in f:
        cqs.append(json.loads(line))


with open(INPUT_CSV, "r", encoding="utf-8") as infile, \
     open(OUTPUT_CSV, "w", encoding="utf-8", newline="") as outfile:

    writer = csv.writer(outfile)
    writer.writerow([
        "problem_id",
        "problem_text",
        "argument_id",
        "argument_type",
        "argument_text",
        'cqs'
    ])

    infile_read = csv.reader(infile, delimiter=',')


    for line in infile_read:
        
        cq_string = ''
        for scheme in cqs:
            if scheme['name'] == line[3]:
                for c in scheme['cq']:
                    cq_string += c + '\n'

        line.append(cq_string)

        writer.writerow(line)

