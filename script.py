import os
import tempfile
from git import Repo
from anthropic import Anthropic
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

claude = Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
openai_client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))


def clone_repo(repo_url):
    temp_dir = tempfile.mkdtemp()
    Repo.clone_from(repo_url, temp_dir)
    return temp_dir


def read_repo_files(repo_path, max_chars=20000):
    repo_content = ""

    for root, _, files in os.walk(repo_path):
        for file in files:
            if file.endswith((".py", ".md", ".js", ".ts", ".json", ".f90")):

                path = os.path.join(root, file)

                try:
                    with open(path, "r", encoding="utf-8") as f:
                        content = f.read()

                    repo_content += f"\n\n# FILE: {file}\n{content}"

                    if len(repo_content) > max_chars:
                        return repo_content[:max_chars]

                except:
                    pass

    return repo_content


def generate_with_claude(repo_content):

    prompt = f"""
Generate structured markdown documentation for this repository.

Include:
- Overview
- Features
- Folder structure
- Important components
- Improvements

{repo_content}
"""

    response = claude.messages.create(
        model="claude-3-7-sonnet-latest",
        max_tokens=2000,
        messages=[{"role": "user", "content": prompt}],
    )

    return response.content[0].text


def generate_with_chatgpt(repo_content):

    prompt = f"""
Generate structured markdown documentation for this repository.

Include:
- Overview
- Features
- Folder structure
- Important components
- Improvements

{repo_content}
"""

    response = openai_client.chat.completions.create(
        model="gpt-4o-mini-2024-07-18",
        messages=[{"role": "user", "content": prompt}],
    )

    return response.choices[0].message.content


def evaluate(markdown, evaluator):

    prompt = f"""
Evaluate this repository documentation.

Return:
- Score /10
- Strengths
- Weaknesses
- Suggested improvements

{markdown}
"""

    if evaluator == "claude":

        response = claude.messages.create(
            model="claude-3-7-sonnet-latest",
            max_tokens=800,
            messages=[{"role": "user", "content": prompt}],
        )

        return response.content[0].text

    else:

        response = openai_client.chat.completions.create(
            model="gpt-4o-mini-2024-07-18",
            messages=[{"role": "user", "content": prompt}],
        )

        return response.choices[0].message.content


def run_pipeline(repo_url, generator="claude", evaluator="gpt"):

    repo_path = clone_repo(repo_url)

    repo_content = read_repo_files(repo_path)

    if generator == "claude":
        markdown = generate_with_claude(repo_content)
    else:
        markdown = generate_with_chatgpt(repo_content)

    with open("repo_summary.md", "w") as f:
        f.write(markdown)

    evaluation = evaluate(markdown, evaluator)

    print("\n=== Evaluation ===\n")
    print(evaluation)


if __name__ == "__main__":

    repo_url = input("Repo URL: ")

    generator = input("Generator (claude/gpt): ").lower()
    evaluator = input("Evaluator (claude/gpt): ").lower()

    run_pipeline(repo_url, generator, evaluator)