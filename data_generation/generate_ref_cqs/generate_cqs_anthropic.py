import json
import tqdm
import re
import anthropic
import yaml
from tenacity import (
    retry,
    stop_after_attempt,
    wait_random_exponential,
)  # for exponential backoff
import os
import csv


def output_cqs(model_name, prompt, client):
    # how to retry when we reach the limit
    @retry(wait=wait_random_exponential(min=1, max=120), stop=stop_after_attempt(12))
    def completion_with_backoff(**kwargs):
        return client.messages.create(**kwargs)

    message = completion_with_backoff(
                                                model=model_name,
                                                max_tokens=1000,
                                                temperature=0,
                                                messages=[{
                                                            "role": "user",
                                                            "content": [
                                                                {"type": "text", "text": prompt}
                                                            ]
                                                        }])
    
    out = message.content[0].text

    return out


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

    model_name = "claude-sonnet-4-6"

    INPUT_CSV = "data/recursive_cqs_generation/0_recursive_cqs_generation - base_set.csv"
    OUTPUT_CSV = "data/recursive_cqs_generation/1_"+model_name+".csv"  

    prompt = """Suggest 5 critical questions that should be raised before accepting the argument in this text:
                
                Text: {context} "{argument}"
                
                Give one question per line. Make the questions simple, and do not give any explanation reagrding why the question is relevant."""

    client = anthropic.Anthropic(api_key=os.environ.get('CLAUDE_API_KEY'),)

    with open(INPUT_CSV, "r", encoding="utf-8") as infile, \
     open(OUTPUT_CSV, "w", encoding="utf-8", newline="") as outfile:

        writer = csv.writer(outfile)
        infile_read = list(csv.reader(infile, delimiter=','))
        writer.writerow(infile_read[0])

        for line in infile_read[1:]:
            answer = output_cqs(model_name, 
                            prompt.format(**{'context':line[5].strip(),
                                            'argument': line[6].strip()}), 
                            client)
            print(answer)
            #line['cqs'] = structure_output(cqs)
            #line.append(answer)

            transformed = False
            if line[8] != line[9]:
                transformed = True

            added = False
            if line[11]:
                added = True
                line[9] += '\n'+line[11]


            line[8] = line[9]


            line[10]=answer

            line[11]=''
            line[12]=''
            line[13]=str(transformed)+str(added)
            #line[14]=''

            writer.writerow(line)
            #exit()


if __name__ == "__main__":
        main()