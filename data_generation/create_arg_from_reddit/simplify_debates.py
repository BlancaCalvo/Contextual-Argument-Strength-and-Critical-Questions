
import re
import json
from tqdm import tqdm
from langchain_openai import ChatOpenAI
import os

api_key = os.environ.get('OPENAI_API_KEY')


# =========================
#  MAIN
# =========================

if __name__ == "__main__":

    with open("data/1_reddit_debates2.jsonl", "r") as f:
        data = []
        for l in f:
            data.append(json.loads(l))

    subreddits = []
    for line in data:
        print(line['title'], line.keys())
        subreddits.append(line['subreddit'])
    topics = list(set(subreddits))


    # TODO: for every subreddit, 

    prompt =  """
    
    Take the 10 situations exposed bellow, read them, and generate two or three simplified situations of the kind of issues that people ask about. Do not use personal names, brand names or product names. 
    For instance, in a story like "Should I buy a Nexus 2000 or a MacBook Air?", just say "I am considering if buying computer A or B. Which one should I buy?". 
    Basically, I want this to look like synthetic examples of debates for a school textbook. 
    I want you to generate the following information. 
    PROBLEM: Here you should expose the simplified question (e.j. "Should I buy a new or a used car?", "Should I use sunglasses on a cloudy day?")
    ARGUMENTS: Write up to 5 arguments that people has given or could be given. Write them in a way that fits one of these argumentation schemes:
- Argument from Sign
- Argument from Example
- Argument from Verbal Classification
- Argument from Position to Know
- Argument from Expert Opinion
- Argument from Cause to Effect
- Argument from Consequences
- Argument from Analogy
- Argument from Popular Opinion
- Argument from Popular Practice
- Argument from Bias
- Generic Ad Hominem
- Practical Reasoning
- Argument from Alternatives
- Argument from Danger Appeal
- Argument from Values
- Argument from Fear Appeal
- Circumstantial Ad Hominem

    Remember: 
    - Do not use brand or product names, but rather "I am considering computer A or B", "B has the advantage of being very fast".
    - Simplify the problem and the vocabulary: do not use technical terms that can not be understood by an average person. 
    - Use the references to get ideas, but create a fictional situations and arguments. 
    - Make the situations as different from each other as possible.
    - The topics of discussion should be as domestic as possible. The best topics are the ones that most people could encounter. 
    - Specify what are we talking about. Right: "Should I buy a manual or a robot vacuum?" Wrong: "Should I choose mechanical or electric products?". The second one is wrong because it does not specify an actual product. 
    - Make the arguments short, do not give many arguments in one. 
    - Indicate which argumentation scheme you are using.

    Example situations: 

    """

    story_structure = """ SITUATION: {title} 
    DESCRIPTION: {text}
    ARGUMENTS: {answers}

    ---------------------------------------------------

    """
    situations = []
    for topic in topics:
        situation = prompt
        for line in data:
            if line['subreddit'] == topic:
                answers = ''
                for answer in line['arguments']:
                    answers+= '\n' +answer['body']

                content = story_structure.format(**{'title':line['title'],
                                                    'text': line['body'],
                                                    'answers': answers}) 
                situation += content
        situations.append(situation)

    print(situations)

    llm = ChatOpenAI(model="gpt-5", api_key=api_key) #gpt-4o-mini

    with open("data/2_simplified_debates2.jsonl", "w", encoding="utf-8") as f:
        for i,s in enumerate(situations):
            response = llm.invoke(s)
            answer = response.content

            f.write(json.dumps({'subreddit':topics[i],'situation': answer}, ensure_ascii=False) + "\n")