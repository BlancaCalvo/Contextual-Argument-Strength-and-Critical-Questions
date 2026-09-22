import json
from collections import Counter

def analyze():
    with open('experiment_app/data/arguments_with_answers.json') as f:
        data = json.load(f)
    
    print(f"Total: {len(data)}")
    print("Schemes:", Counter(d.get('scheme') for d in data))
    print("Topics:", Counter(d.get('topic') for d in data))
    print("Labels:", Counter(d.get('label (automated)') for d in data))

if __name__ == "__main__":
    analyze()
