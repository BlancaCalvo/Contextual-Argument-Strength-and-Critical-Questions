import json
import csv
import re

INPUT_JSONL = "data/2_simplified_debates2.jsonl"
OUTPUT_CSV = "data/3_to_choose2.csv"

with open('data/walton_plus.jsonl') as f:
    cqs = []
    for line in f:
        cqs.append(json.loads(line))

argument_header_re = re.compile(r"\(.*\)|\[.*\]")#, r"Argument from .*:")

problem_id = 0
argument_id = 0

with open(INPUT_JSONL, "r", encoding="utf-8") as infile, \
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

    for line in infile:
        if not line.strip():
            continue

        data = json.loads(line)

        situations = data['situation'].split('PROBLEM:')

        if len(situations) > 1:
            for situation in situations[1:]:
                problem, arguments=situation.split('ARGUMENTS:')
                if arguments:

                    problem_id += 1
                    problem_text = problem
                    print(arguments)
                    

                    # Split arguments on blank lines
                    arguments = arguments.strip().lstrip("SITUATION").strip()
                    raw_arguments = arguments.split('\n')
                    print(raw_arguments)

                    for raw_arg in raw_arguments[1:]:
                        raw_arg = raw_arg.strip().lstrip("-").strip()
                        if not raw_arg:
                            continue

                        match = argument_header_re.search(raw_arg)
                        arg_type = ''
                        if not match:
                            # Fallback if format is unexpected
                            if re.search(r"(.*): ", arg_text):
                                arg_type2 = re.search(r"(.*): ", arg_text).group(0).strip()
                                arg_text = arg_text.replace(arg_type2, '').strip()
                                if not arg_type:
                                    arg_type = arg_type2.replace(':', '').strip()
                            else:
                                arg_type = "Unknown"
                                arg_text = raw_arg
                        else:
                            arg_type = match.group(0).strip()
                            arg_text = match.string.strip().replace(arg_type, '')
                            arg_type = arg_type.replace('(', '').replace(')', '').replace('[', '').replace(']', '')
                            if re.search(r"(.*): ", arg_text):
                                arg_type2 = re.search(r"(.*): ", arg_text).group(0).strip()
                                arg_text = arg_text.replace(arg_type2, '').strip()
                                if not arg_type:
                                    arg_type = arg_type2.replace(': ', '')
                            print(arg_text)
                            print(arg_type)

                        argument_id += 1

                        cq_string = ''
                        for scheme in cqs:
                            if scheme['name'] == arg_type:
                                for c in scheme['cq']:
                                    cq_string += c + '\n'

                        writer.writerow([
                                problem_id,
                                problem_text,
                                argument_id,
                                arg_type,
                                arg_text,
                                cq_string
                            ])
                else:
                    print('missed arguments', situation)
        else:
            print('missed situations', situations)

print("Conversion complete.")
