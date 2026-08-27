import praw
import re
import json
from tqdm import tqdm
from prawcore.exceptions import NotFound, Forbidden
from collections import defaultdict
import os

# =========================
#  REDDIT API CONFIG
# =========================

reddit = praw.Reddit(
    client_id=os.environ.get('REDDIT_CLIENT'),
    client_secret=os.environ.get('REDDIT_SECRET'),
    user_agent="contextual-decision-dataset/0.1"
)

# =========================
#  TARGET SUBREDDITS
# =========================

SUBREDDITS = [
    "laptops",
    "personalfinance",
    "frugal",
    "buyitforlife",
    "homeimprovement",
    "careeradvice",
    "jobs",
    "entrepreneur",
    "homelab",
    "diy",
    "smallbusiness",
    "nutrition",
    "eatcheapandhealthy",
    "running",
    "languagelearning",
    "gradschool",
    "ultralight"
]

MAX_PER_TOPIC = {
    "laptops": 10,
    "homeimprovement": 10,
    "personalfinance": 10,
    "frugal": 10,
    "buyitforlife": 10,
    "careeradvice": 10,
    "jobs": 10,
    "entrepreneur": 10,
    "homelab": 10,
    "diy": 10,
    "smallbusiness": 10,
    "nutrition": 10,
    "eatcheapandhealthy": 10,
    "running": 10,
    "languagelearning": 10,
    "gradschool": 10,
    "ultralight": 10
}


# =========================
#  DECISION QUESTION FILTER
# =========================

DECISION_PATTERNS = [
    r"should i .* or .*",
    r"\bvs\.?\b",
    r"which .* better",
    r"new or used",
    r"choose between",
    r"recommend .* between",
    r"a or b",
]

def is_decision_post(text: str) -> bool:
    text = text.lower()
    return any(re.search(p, text) for p in DECISION_PATTERNS)

# =========================
#  CONTEXTUAL ARGUMENT FILTER
# =========================

CONTEXT_MARKERS = [
    "if ",
    "when ",
    "depends on",
    "as long as",
    "in your case",
    "given that",
    "because",
    "unless",
]

def is_contextual_argument(text: str) -> bool:
    text = text.lower()
    return any(marker in text for marker in CONTEXT_MARKERS)

# =========================
#  FETCH POSTS
# =========================

def fetch_decision_posts(limit_per_subreddit=200):
    posts = []

    for sub in SUBREDDITS:
        subreddit = reddit.subreddit(sub)
        try:
            for submission in subreddit.new(limit=10):
                print(submission.title)
                for submission in subreddit.new(limit=limit_per_subreddit):
                    combined_text = f"{submission.title} {submission.selftext}"
                    if is_decision_post(combined_text):
                        posts.append(submission)
        except NotFound:
            print(f"Subreddit {sub} not found (404). Skipping.")
        except Forbidden:
            print(f"Subreddit {sub} is private or banned. Skipping.")
        

    return posts

# =========================
#  EXTRACT CONTEXTUAL COMMENTS
# =========================

def extract_contextual_comments(submission, min_score=1):
    submission.comments.replace_more(limit=0)
    arguments = []

    for comment in submission.comments.list():
        if (
            comment.body
            and comment.score >= min_score
            and is_contextual_argument(comment.body)
        ):
            arguments.append({
                "comment_id": comment.id,
                "body": comment.body,
                "score": comment.score
            })

    return arguments


def build_diverse_dataset():
    dataset = []
    topic_counts = defaultdict(int)

    posts = fetch_decision_posts()

    for post in tqdm(posts, desc="Processing posts"):
        topic = post.subreddit.display_name
        if topic_counts[topic] >= MAX_PER_TOPIC.get(topic, 10):
            continue  # skip if we already have enough from this topic

        args = extract_contextual_comments(post)

        if len(args) >= 2:
            dataset.append({
                "post_id": post.id,
                "subreddit": topic,
                "title": post.title,
                "body": post.selftext,
                "score": post.score,
                "num_comments": post.num_comments,
                "arguments": args
            })
            topic_counts[topic] += 1

        # stop early if all topics filled
        if all(topic_counts.get(k,0) >= v for k,v in MAX_PER_TOPIC.items()):
            break

    return dataset


# =========================
#  MAIN
# =========================

if __name__ == "__main__":
    dataset = build_diverse_dataset()

    with open("data/1_reddit_debates2.jsonl", "w", encoding="utf-8") as f:
        for item in dataset:
            f.write(json.dumps(item, ensure_ascii=False) + "\n")

    print(f"Saved {len(dataset)} contextual decision discussions.")
