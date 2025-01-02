#!/usr/bin/env python3

import openai
import os
import json
import time

# ===============================================
# Configuration
# ===============================================

# (1) Provide your OpenAI API key (or ensure it is set in your environment).
openai.api_key = os.getenv("OPENAI_API_KEY", "sk-REPLACE_WITH_YOUR_KEY")

# (2) Path to a JSON file that we use for storing bullet items that we've already processed.
CACHE_FILE = "processed_bullets.json"

# (3) Path to the text file containing bullet items, one per line.
# You can generate or manually create a file with each bullet item in your list.
BULLET_LIST_FILE = "open_problems_bullets.txt"

# (4) Model to use:
GPT_MODEL = "gpt-4o"  # or "gpt-4-32k" if you have access, etc.

# (5) A template prompt that you'll send for each bullet.
# We'll pass the bullet text in {bullet}. Adjust as needed.
PROMPT_TEMPLATE = """You're given a single open problem item from a Wiki bullet list:

"{bullet}"

Please output a file in the following format:

===={{file_name}}.md
---
layout: problem
title: "{{title}}"
status: "Unsolved"
wiki_url: "https://en.wikipedia.org/wiki/{{title_snake}}"
problem_posed: ""
date_solved:
solver:
notes:
---
A short description that stands on its own, but does not repeat the name of the problem verbatim. Summarize it nicely.


Notes:
1) Replace {{file_name}}, {{title}}, and {{title_snake}} with appropriate values based on the bullet content.
2) If you know the year which the problem was posed, fill it in the "problem posed" year, leave it blank otherwise.
3) If the problem in the  bullet text is not solved yet, keep the solved date or solver blank.
4) Make the short description one paragraph at most.
5) If the bullet text does not give you enough information, do your best guess or leave placeholders.
6) Do not add any other text to the output, just the format above.
7) Do not include markdown code block ticks in the output.
"""

# (6) How long to wait (in seconds) between calls to avoid rate limits.
SLEEP_BETWEEN_CALLS = 1.0

# ===============================================
# Script logic
# ===============================================

def load_processed_bullets():
    """Load the list of bullets we have already processed from CACHE_FILE."""
    if not os.path.exists(CACHE_FILE):
        return set()
    with open(CACHE_FILE, "r", encoding="utf-8") as f:
        return set(json.load(f))

def save_processed_bullets(processed_set):
    """Save the updated set of processed bullets into CACHE_FILE."""
    with open(CACHE_FILE, "w", encoding="utf-8") as f:
        json.dump(list(processed_set), f)

def get_completion(prompt):
    """Send the prompt to GPT-4 and return the text completion."""
    try:
        client = openai.OpenAI()
        response = client.chat.completions.create(
            model=GPT_MODEL,
            messages=[
                {"role": "system", "content": "You are a helpful assistant."},
                {"role": "user", "content": prompt}
            ],
        )
        return response.choices[0].message.content
    except Exception as e:
        print(f"OpenAI API error: {e}")
        return None

def generate_file_from_bullet(bullet_text):
    """
    Given a bullet text, craft a prompt and call GPT-4 for the final output in the required format.
    """
    # You may want to guess a short filename or title from bullet_text
    # For demonstration, let's do a naive approach:
    #  - We'll just take the first 5 words, snake_case them,
    #  - if bullet is shorter, fallback
    words = bullet_text.split()
    short_title_list = words[:5] if len(words) >= 5 else words
    # Clean them up for a snake case
    short_title_list = [w.lower().strip(",.!?;:'\"()") for w in short_title_list]
    file_stem = "_".join(short_title_list)

    # Example for GPT prompt: we place bullet into {bullet}
    # GPT is asked to fill placeholders {file_name}, {title}, {title_snake}, etc.
    # The script won't finalize them; we rely on GPT to do that
    prompt = PROMPT_TEMPLATE.format(bullet=bullet_text)

    completion = get_completion(prompt)
    return completion


def main():
    # Load the set of processed bullet items (to skip reprocessing)
    processed = load_processed_bullets()

    # Open the file containing bullet items
    with open(BULLET_LIST_FILE, "r", encoding="utf-8") as f:
        bullets = [line.strip() for line in f if line.strip()]

    # For each bullet, if not processed, do it
    for bullet in bullets:
        if bullet in processed:
            print(f"Skipping already processed bullet: {bullet[:60]}...")
            continue

        print(f"Processing bullet: {bullet[:60]}...")
        content = generate_file_from_bullet(bullet)

        # If we got some content, let's store it in a .md file
        # (extracted from the "====filename.md" line if possible).
        if content:
            lines = content.splitlines()
            # This is all a guess: we assume GPT's first line is "====some_name.md"
            # We'll parse that, then store the subsequent lines to a file
            potential_filename = "UNKNOWN.md"
            output_lines = []

            for line in lines:
                if line.startswith("====") and line.endswith(".md"):
                    # e.g. "====collatz_conjecture.md"
                    potential_filename = line.strip("= \n")
                else:
                    output_lines.append(line)

            with open(potential_filename, "w", encoding="utf-8") as outf:
                outf.write("\n".join(output_lines))
            print(f"Saved to file: {potential_filename}")

            # Update processed set
            processed.add(bullet)
            save_processed_bullets(processed)

            # Sleep to not exceed rate limits
            time.sleep(SLEEP_BETWEEN_CALLS)
        else:
            print("No content returned for bullet. Skipping ...")

    print("Done!")


if __name__ == "__main__":
    main()
