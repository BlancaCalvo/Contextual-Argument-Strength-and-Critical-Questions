import json
import random
from collections import Counter

def score_groups(groups):
    """Calculate a 'badness' score for the groups. Lower is better."""
    score = 0
    
    for g in groups:
        # Check avg rating distribution (target: 2 items from each tier)
        tier_counts = Counter(d['tier'] for d in g)
        for tier in range(3):
            score += abs(tier_counts[tier] - 2) * 5 # Weight this heavily
        
        # Topic diversity
        t_counts = Counter(d['topic'] for d in g)
        for t, c in t_counts.items():
            if c > 2: score += (c - 2) * 2 # Penalize same topic > 2
            
        # Scheme diversity
        s_counts = Counter(d['scheme'] for d in g)
        for s, c in s_counts.items():
            if c > 2: score += (c - 2) * 2 # Penalize same scheme > 2
            
    return score

def balanced_split():
    with open('experiment_app/data/arguments_with_answers.json') as f:
        data = json.load(f)
    
    # Assign tiers based on avg rating rank
    # 32 arguments total, exclude 2, 3 tiers of 10
    data.sort(key=lambda x: float(x['avg']))
    
    #excluded = [data.pop(0), data.pop(-1)]
    #print(f"Excluded arguments (IDs): {[d['id'] for d in excluded]}")
    #print(f"Excluded ratings: {[d['avg'] for d in excluded]}")

    for i, d in enumerate(data):
        d['tier'] = i // 10
    
    best_score = float('inf')
    best_groups = None
    
    # Try 10000 random permutations to find a good one
    for _ in range(10000):
        random.shuffle(data)
        candidate_groups = [data[i*6:(i+1)*6] for i in range(5)]
        current_score = score_groups(candidate_groups)
        
        if current_score < best_score:
            best_score = current_score
            best_groups = candidate_groups
            if best_score == 0: break
            
    # Output
    for i, group in enumerate(best_groups):
        output_file = f"experiment_app/data/arguments_group_{i+1}.json"
        with open(output_file, 'w') as f:
            json.dump(group, f, indent=2)
        
        group_avg = sum(float(d['avg']) for d in group) / len(group)
        tiers = Counter(d['tier'] for d in group)
        print(f"Group {i+1} saved. Mean Avg: {group_avg:.2f}. Tiers: {dict(tiers)}")

    print(f"Best total score: {best_score}")

if __name__ == "__main__":
    balanced_split()
