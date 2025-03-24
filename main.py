import os
import subprocess
import sys
from git import Repo
from openai import OpenAI
import os

api_key = os.getenv("OPENAI_API_KEY")
if not api_key:
    print("⚠️ Error: OPENAI_API_KEY environment variable not set!")
    sys.exit(1)

client = OpenAI(api_key=api_key)

# Initialize Repo
repo = Repo(os.getcwd())

def get_conflicted_files():
    """Returns a list of files with merge conflicts."""
    output = subprocess.run(["git", "diff", "--name-only", "--diff-filter=U"], capture_output=True, text=True)
    conflicted_files = output.stdout.strip().split("\n") if output.stdout else []
    
    if conflicted_files:
        print(f"Conflicted files: {conflicted_files}")
    else:
        print("No conflicts detected.")
    return conflicted_files


def ai_suggest_resolution(file_path):
    """Uses AI to suggest a resolution for the given conflicted file."""
    try:
        with open(file_path, "r") as file:
            content = file.read()

        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "You are an AI Git assistant. If the resolution is obvious, apply it. If not, return 'UNSURE' so the user can decide."},
                {"role": "user", "content": f"Resolve the following Git merge conflict automatically. Do not provide explanations, only return the final resolved file:\n{content}"}
            ]
        )

        resolution = response.choices[0].message.content
        if resolution == "UNSURE":
            print(f"⚠️ AI was unsure about resolving {file_path}. Please review manually.")
            return None

        # Apply the resolution if AI returned a valid answer
        with open(file_path, "w") as file:
            file.write(resolution)

        print(f"✔ AI resolution applied to {file_path}")
        return resolution

    except Exception as e:
        print(f"⚠️ Error resolving conflict in {file_path}: {e}")
        return None


def apply_ai_resolutions():
    """Iterate through conflicted files and apply AI suggestions."""
    conflicted_files = get_conflicted_files()

    if not conflicted_files:
        print("No conflicts detected!")
        return

    for file in conflicted_files:
        print(f"Processing conflict in: {file}")
        resolution = ai_suggest_resolution(file)

        if resolution:
            with open(file, "w") as f:
                f.write(resolution)

            print(f"✔ AI resolution applied to {file}")
        else:
            print(f"⚠️ Could not resolve conflict in {file}.")

    # Stage resolved files and continue rebase
    subprocess.run(["git", "add"] + conflicted_files)
    print("✅ Conflicts resolved! Rebase continued.")


def ai_rebase(target_branch="main"):
    """Runs an AI-assisted rebase against the target branch."""
    print(f"🔄 Starting AI-assisted rebase onto {target_branch}...")
    try:
        subprocess.run(["git", "fetch", "origin"], check=True)
        subprocess.run(["git", "rebase", f"origin/{target_branch}"], check=True)
    except subprocess.CalledProcessError:
        print("⚠️ Rebase encountered conflicts. Running AI resolution...")
        conflicted_files = get_conflicted_files()  # Check for conflicts
        if conflicted_files:
            apply_ai_resolutions()  # Apply AI resolutions only if conflicts exist
        else:
            print("No conflicts found, rebase completed successfully.")

def main():
    if len(sys.argv) < 2:
        print("Usage: git-ai <command>")
        return

    command = sys.argv[1]

    if command == "resolve":
        apply_ai_resolutions()
    elif command == "rebase":
        target_branch = sys.argv[2] if len(sys.argv) > 2 else "main"
        ai_rebase(target_branch)
    else:
        print("Unknown command. Available commands: resolve, rebase")

if __name__ == "__main__":
    main()
