from pathlib import Path
import json
import re

PUBLIC_QUIZ_FILE = Path(__file__).resolve().parents[2] / "quizzes" / "public"
USED_PEOPLE_FILE = PUBLIC_QUIZ_FILE / "used_people.txt"
UNUSED_PEOPLE_FILE = PUBLIC_QUIZ_FILE / "unused_people.txt"



def read_used_people() -> list[str]:
    people = []
    with open(USED_PEOPLE_FILE, 'r') as f:
        for p in f.readlines():
            stripped_p = p.strip()
            if stripped_p:
                people.append(stripped_p)

    return people


def _get_published_quizzes() -> list[Path]:
    return sorted(list(PUBLIC_QUIZ_FILE.glob('*.html')))


def _get_names_from_quiz(file_path: Path) -> list[str]:
    """Reads an HTML file from a Path object and extracts the names

    of people from the 'rounds' array.
    """
    # Ensure the path exists before attempting to read
    if not file_path.is_file():
        raise FileNotFoundError(f"No file found at: {file_path}")

    # Read the text content of the file
    html_content = file_path.read_text(encoding="utf-8")

    # Find where the 'rounds' array starts
    match = re.search(r"const\s+rounds\s*=\s*\[", html_content)
    if not match:
        return []

    # Get the index of the opening bracket '['
    start_index = match.end() - 1

    try:
        # Safely parse only the valid JSON array starting from that index
        rounds, _ = json.JSONDecoder().raw_decode(html_content, idx=start_index)

        # Extract the 'person' field from each round
        return [round_data["person"] for round_data in rounds if "person" in round_data]
    except (json.JSONDecodeError, KeyError, TypeError):
        return []
    

def update():
    published_quizzes = _get_published_quizzes()

    all_used_names = []
    for quiz in published_quizzes:
        print(f"analysing quiz {quiz}")

        names = _get_names_from_quiz(quiz)

        if len(set(names)) != len(names):
            print("Duplicate names found in quiz")
        
        for name in names:
            if name in all_used_names:
                print(f"name {name} already in use!")
            else:
                all_used_names.append(name)

    with open(USED_PEOPLE_FILE, 'w'):
        USED_PEOPLE_FILE.write_text('\n'.join(all_used_names))

    return



def main():
    update()

if __name__ == "__main__":
    print(read_used_people())
    #main()