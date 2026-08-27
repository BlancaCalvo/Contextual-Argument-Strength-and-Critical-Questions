

## Create context that give arguments a certain strength

```

python generate_structured_context_claude.py
# generates context by assigning a label to each argument and generating a response for each critical question.

```

We assign a label to each argument and generate a response for each critical question.

For each label, we define a distribution of response types:
- strong: 2-3 irrefutable, rest neutral
- reasonable: 70% favorable, 30% neutral
- weak: 30% favorable, 70% neutral
- not supported: 2-3 invalidating, rest neutral

Response types:
- irrefutable: A fact that makes the argument practically irrefutable in this context. The fact should strongly support the key premises of the argument, leaving almost no room for doubt.
- favorable: A fact that supports the argument in this context. The fact should back up one of the argument's premises, but not so strongly that it removes all doubt.
- undermining: A fact that undermines the argument in this context. The fact should cast doubt on one of the argument's premises, but not so strongly that it makes the argument completely implausible.
- neutral: A fact that is relevant to the situation but does not affect the strength of the argument in either direction.
- invalidating: A fact that directly contradicts or invalidates a key premise of the argument in this context, making the argument very hard to sustain.

Each answer is generated independently, but we keep track of the previously generated responses to ensure coherence. Finally, a neutral background paragraph is generated to complete the context.
