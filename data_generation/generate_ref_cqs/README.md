# Reference CQs Generation

This directory contains scripts to generate a comprehensive set of reference Critical Questions (CQs) iteratively using multiple LLMs.

## Data Workflow

The datasets in `data/recursive_cqs_generation/` follow a numeric order showing the iteration process. Each automated generation is followed by a manual review/annotation step (prefixed with `recursive_cqs_generation - `).

0. **Theory CQs**: `0_recursive_cqs_generation - base_set.csv`
1. **Claude-3-Sonnet**:
   - Output: `1_claude-sonnet-4-6.csv`
   - Manual Correction: `1_recursive_cqs_generation - claude-sonnet-4-6.csv`
2. **GPT-4o**:
   - Output: `2_gpt-4o-2024-08-06.csv`
   - Manual Correction: `2_recursive_cqs_generation - gpt-4o-2024-08-06.csv`
3. **Gemma-2-27b**:
   - Output: `3_google_gemma-2-27b-it.csv`
   - Manual Correction: `3_recursive_cqs_generation - google_gemma-2-27b-it.csv`
4. **Llama-3-70b**:
   - Output: `4_meta-llama_Meta-Llama-3-70B-Instruct.csv`
   - Manual Correction: `4_recursive_cqs_generation - Meta-Llama-3-70B.csv`
5. **Final Curation**: `5_final.csv`
6. **Adaptation with Names**: `6_final_with_names.csv`

## Scripts

- `add_theory_cqs.py`: Adds initial CQs based on Walton's schemes.
- `generate_cqs_anthropic.py`: Iteration using Claude.
- `generate_cqs_openai.py`: Iteration using GPT-4o.
- `generate_cqs_hf.py`: Iteration using HuggingFace models (Llama, Gemma).
- `adapt_cqs_to_situation.py`: Final step to add character names to questions.
