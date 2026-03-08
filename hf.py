import os
import tempfile
from git import Repo
from huggingface_hub import InferenceClient
from dotenv import load_dotenv

load_dotenv()

HF_TOKEN = os.getenv("HF_TOKEN")

# Initialize inference client
generator_client = InferenceClient(
    model="Qwen/Qwen2.5-7B-Instruct",
    token=HF_TOKEN
)

evaluator_client = InferenceClient(
    model="openai/gpt-oss-120b",
    token=HF_TOKEN
)


def clone_repo(repo_url):
    temp_dir = tempfile.mkdtemp()
    Repo.clone_from(repo_url, temp_dir)
    return temp_dir


def read_repo_files(repo_path, max_chars=20000):
    repo_content = ""

    for root, _, files in os.walk(repo_path):
        if ".git" in root or "node_modules" in root:
            continue

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


def generate_markdown(repo_content):

    prompt = f"""
Generate structured Markdown documentation for this repository.

Include:
- Project Overview
- Key Features
- Folder Structure
- Important Files
- How it works
- Improvements

Repository content:
{repo_content}
"""

    response = generator_client.chat_completion(
        messages=[
            {"role": "user", "content": prompt}
        ],
        max_tokens=1200,
        temperature=0.3
    )

    return response.choices[0].message.content


def evaluate_markdown(markdown):

    prompt = f"""
Evaluate this repository documentation.

Return:
Score: /10
Strengths:
Weaknesses:
Improvements:

Markdown:
{markdown}
"""

    response = evaluator_client.chat_completion(
        messages=[
            {"role": "user", "content": prompt}
        ],
        max_tokens=600,
        temperature=0.2
    )

    return response.choices[0].message.content


def run_pipeline(repo_url):

    print("Cloning repo...")
    repo_path = clone_repo(repo_url)

    print("Reading repo...")
    repo_content = read_repo_files(repo_path)

    print("Generating markdown...")
    markdown = generate_markdown(repo_content)

    with open("repo_summary.md", "w") as f:
        f.write(markdown)
    # markdown = open("repo_summary.md", "r")

    print("Evaluating markdown...")
    evaluation = evaluate_markdown(markdown)

    print("\n===== EVALUATION =====\n")
    print(evaluation)


if __name__ == "__main__":
    repo_url = input("GitHub repo URL: ")
    run_pipeline(repo_url)