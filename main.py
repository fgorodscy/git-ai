import os
import subprocess
import sys
from git import Repo
from openai import OpenAI
import os

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# Initialize Repo
repo = Repo(os.getcwd())

def get_conflicted_files():
    """Returns a list of files with merge conflicts."""
    output = subprocess.run(["git", "diff", "--name-only", "--diff-filter=U"], capture_output=True, text=True)
    return output.stdout.strip().split("\n") if output.stdout else []

def ai_suggest_resolution(file_path):
    """Uses AI to suggest a resolution for the given conflicted file."""
    with open(file_path, "r") as file:
        content = file.read()

    
    response = client.chat.completions.create(
    model="gpt-4o-mini",
    messages=[
        {"role": "system", "content": "You are an AI Git assistant. If the resolution is obvious, apply it. If not, return 'UNSURE' so the user can decide."},
        {"role": "user", "content": f"Resolve the following Git merge conflict automatically. Do not provide explanations, only return the final resolved file:\n{content}"}
    ]
)


    return response.choices[0].message.content

def apply_ai_resolutions():
    """Iterate through conflicted files and apply AI suggestions."""
    conflicted_files = get_conflicted_files()

    if not conflicted_files:
        print("No conflicts detected!")
        return

    for file in conflicted_files:
        print(f"Processing conflict in: {file}")
        resolution = ai_suggest_resolution(file)

        with open(file, "w") as f:
            f.write(resolution)

        print(f"✔ AI resolution applied to {file}")

    subprocess.run(["git", "add"] + conflicted_files)
    print("✅ Conflicts resolved! Run 'git commit' to finalize the changes.")

def ai_rebase(target_branch="main"):
    """Runs an AI-assisted rebase against the target branch."""
    print(f"🔄 Starting AI-assisted rebase onto {target_branch}...")
    try:
        subprocess.run(["git", "fetch", "origin"], check=True)
        subprocess.run(["git", "rebase", f"origin/{target_branch}"], check=True)
    except subprocess.CalledProcessError:
        print("⚠️ Rebase encountered conflicts. Running AI resolution...")
        apply_ai_resolutions()

def main():
    if len(sys.argv) < 2:
        print("Usage: git-ai <command>")
        return

    command = sys.argv[1]

    if command == "resolve":
        apply_ai_resolutions()
    elif command == "rebase":
        ai_rebase()
    else:
        print("Unknown command. Available commands: resolve, rebase")

if __name__ == "__main__":
    main()
