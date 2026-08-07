from pathlib import Path


def load_prompt(prompt_name: str):
    prompt_path = Path(__file__).parents[1]/'prompts'/f"{prompt_name}.prompt"
    return prompt_path.read_text(encoding="utf-8")

if __name__ == "__main__":
    prompt = load_prompt("correct_sql")
    print(prompt)
