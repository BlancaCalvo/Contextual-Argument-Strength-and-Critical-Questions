
import re
import csv
from transformers import AutoTokenizer, AutoModelForCausalLM, GenerationConfig, AutoProcessor
import torch


def output_cqs(model_name, prompt, model, tokenizer, new_params=False, remove_instruction=True):

    chat = [{"role": "user", "content": prompt}] 
    chat_formated = tokenizer.apply_chat_template(chat, tokenize=False)
    inputs = tokenizer(chat_formated, return_tensors="pt")

    inputs = inputs.to('cuda')

    if new_params:
        generated_ids = model.generate(**inputs, **new_params) # use if we want to give specific params
    else:
        generated_ids = model.generate(**inputs, max_new_tokens=512) 

    generated_ids = [output_ids[len(input_ids):] for input_ids, output_ids in zip(inputs.input_ids, generated_ids)] # remove everything that is not newly generated

    out = tokenizer.batch_decode(generated_ids, skip_special_tokens=True)[0]

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

    if 'gemma' in model_name:
        INPUT_CSV = "data/recursive_cqs_generation/2_recursive_cqs_generation - gpt-4o-2024-08-06.csv"
    else:
        INPUT_CSV = "data/recursive_cqs_generation/3_recursive_cqs_generation - google_gemma-2-27b-it.csv"

    number = "3_" if "gemma" in model_name else "4_"
    OUTPUT_CSV = "data/recursive_cqs_generation/" + number + model_name.replace("/", '_') + ".csv"

    prompt = """Suggest 5 critical questions that should be raised before accepting the argument in this text:
                
                Text: {context} "{argument}"
                
                Give one question per line. Make the questions simple, and do not give any explanation reagrding why the question is relevant."""

    #if 'Qwen' in model_name:
    #    model = Qwen2_5_VLForConditionalGeneration.from_pretrained(model_name, device_map="auto")
    #    tokenizer = AutoProcessor.from_pretrained(model_name)
    if 'gemma' in model_name:
        model = AutoModelForCausalLM.from_pretrained(model_name, device_map="auto", attn_implementation='eager')
        tokenizer = AutoTokenizer.from_pretrained(model_name)
    else:
        model = AutoModelForCausalLM.from_pretrained(model_name, device_map="auto", torch_dtype=torch.bfloat16) # , attn_implementation="flash_attention_2"
        tokenizer = AutoTokenizer.from_pretrained(model_name)


    with open(INPUT_CSV, "r", encoding="utf-8") as infile, \
     open(OUTPUT_CSV, "w", encoding="utf-8", newline="") as outfile:

        writer = csv.writer(outfile)
        infile_read = list(csv.reader(infile, delimiter=','))
        writer.writerow(infile_read[0])

        for line in infile_read[1:]:
            answer = output_cqs(model_name, 
                                prompt.format(**{'context':line[5].strip(),
                                            'argument': line[6].strip()}), 
                                model, tokenizer)
            print(answer)
            line.append(answer)

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
            line[13]=''
            #line[14]=''

            writer.writerow(line)
            #exit()


if __name__ == "__main__":
        main()