"""
Generate fill-in-the-blank questions from existing multiple-choice questions.

Uses programmatic Korean text analysis to create cloze-style questions
by extracting key terms from correct answer options.

Usage:
    python generate_blanks.py                     # Generate for all subjects
    python generate_blanks.py --subject s1        # Single subject
    python generate_blanks.py --copy-to-frontend  # Also copy to public/data/
    python generate_blanks.py --dry-run            # Show stats only
"""

import argparse
import json
import re
import sys
from pathlib import Path


# Korean particles (ordered by length desc for greedy matching)
PARTICLE_PATTERNS = [
    # Multi-char particles (match first for specificity)
    "으로 인해", "로 인해",
    "으로서", "로서", "으로써", "로써",
    "에서는", "에서의", "에서",
    "에게서", "에게는", "에게",
    "에는", "에도", "에만",
    "까지는", "부터는",
    "이란", "이라는", "이라",
    "에 관한", "에 대한", "에 의한", "에 따른",
    "으로는", "으로도", "으로의",
    "로는", "로도", "로의",
    "에 해당", "에 속하",
    # Double particles
    "에서", "까지", "부터", "마다", "조차", "처럼", "같이", "보다",
    # Single-char particles (most common)
    "으로", "로",
    "은", "는", "이", "가",
    "을", "를", "의",
    "와", "과", "도", "만",
]

# Patterns in question content that indicate "wrong answer" questions
WRONG_ANSWER_KW = [
    "틀린", "옳지 않은", "잘못", "부적절", "적절하지", "해당하지",
    "아닌 것", "않는 것", "없는 것",
]

# Short/combination answer patterns to skip
SKIP_PATTERNS = [
    r"^[ㄱ-ㅎ가-힣],?\s*[ㄱ-ㅎ가-힣]$",  # "ㄱ, ㄴ"
    r"^[A-Z]:\s*.+,\s*[A-Z]:",  # "A: X, B: Y"
    r"^\d+[개만원억천백]",  # "2개", "24만원"
    r"^[①②③④⑤]",  # Numbered options
]


def is_wrong_answer_question(content: str) -> bool:
    return any(kw in content for kw in WRONG_ANSWER_KW)


def is_skip_option(option: str) -> bool:
    if len(option) < 15:
        return True
    return any(re.match(p, option.strip()) for p in SKIP_PATTERNS)


def is_valid_answer(term: str) -> bool:
    """Check if a term is a valid fill-in-the-blank answer."""
    # Must be at least 2 chars
    if len(term) < 2:
        return False
    # Must contain Korean characters
    korean_chars = sum(1 for c in term if "\uac00" <= c <= "\ud7a3")
    if korean_chars < 2:
        return False
    # Must not contain parentheses or brackets
    if any(c in term for c in "()[]{}"):
        return False
    # Must not end with verb stems that indicate broken conjugation
    if term[-1] in "하되지시리니키":
        return False
    # Must not be a single-syllable variable like X, A, B
    if len(term) <= 2 and any(c.isascii() for c in term):
        return False
    return True


# Characters before 은/는/이/가 that indicate verb endings (not particles)
VERB_ENDINGS_BEFORE_PARTICLE = set("하되지시리니키오아며고서라나")


def find_blank_term(text: str) -> tuple[str, str, str] | None:
    """Find the best term to blank out from Korean text.

    Returns (content_with_blank, answer_term, remainder) or None.
    """
    candidates = []

    for particle in PARTICLE_PATTERNS:
        # Build pattern: non-whitespace chars (2-15) followed by particle
        escaped = re.escape(particle)
        pattern = rf"([\S]{{2,15}})({escaped})"
        for m in re.finditer(pattern, text):
            term = m.group(1)
            particle_text = m.group(2)

            # Skip invalid answers
            if not is_valid_answer(term):
                continue

            # Skip if term starts with a particle-like char
            if term[0] in "은는이가을를의에":
                continue

            # For single-char particles (은/는/이/가): skip if preceded by verb ending
            if len(particle_text) == 1 and particle_text in "은는이가":
                if term[-1] in VERB_ENDINGS_BEFORE_PARTICLE:
                    continue

            # Skip terms inside parentheses
            before_term = text[: m.start(1)]
            if before_term.count("(") > before_term.count(")"):
                continue

            # Score: prefer 3-8 char terms (likely meaningful Korean nouns)
            term_len = len(term)
            score = 0
            if 3 <= term_len <= 8:
                score += 10
            elif 2 <= term_len <= 12:
                score += 5

            # Prefer terms earlier in the sentence (more likely to be key subject)
            position_score = max(0, 10 - m.start() // 5)
            score += position_score

            # Prefer longer particles (more specific context)
            score += len(particle)

            # Bonus for pure Korean terms
            if all("\uac00" <= c <= "\ud7a3" for c in term):
                score += 3

            content_with_blank = text[: m.start(1)] + "[BLANK]" + text[m.end(1) :]
            candidates.append((score, content_with_blank, term))

    if not candidates:
        return None

    # Return the highest-scoring candidate
    candidates.sort(key=lambda x: -x[0])
    best = candidates[0]
    return best[1], best[2], ""


def create_blank_from_mc(mc_q: dict) -> dict | None:
    """Create a fill-in-the-blank question from an MC question."""
    content = mc_q["content"]
    correct_option = mc_q["options"][mc_q["correctIndex"]]

    # Skip wrong-answer questions
    if is_wrong_answer_question(content):
        return None

    # Skip short/combination options
    if is_skip_option(correct_option):
        return None

    # Clean up the option text (remove trailing artifacts)
    option_text = correct_option.strip()
    option_text = re.sub(r"\s*\d{4}년\s*제\d+회.*$", "", option_text)  # Remove exam refs

    # Try to find a good term to blank out
    result = find_blank_term(option_text)
    if result is None:
        return None

    blank_content, answer, _ = result

    # Validate: [BLANK] must appear exactly once
    if blank_content.count("[BLANK]") != 1:
        return None

    # Validate: answer should be meaningful (2-15 chars)
    if len(answer) < 2 or len(answer) > 15:
        return None

    # Validate: remaining content should be meaningful (at least 10 chars without blank)
    remaining = blank_content.replace("[BLANK]", "").strip()
    if len(remaining) < 10:
        return None

    # Extract topic from question for explanation context
    topic_match = re.search(
        r"(.{5,40}?)(?:에 관한|에 대한|으로서|의 경우)", content
    )
    topic = topic_match.group(1).strip() if topic_match else ""

    explanation = f"{topic + ' — ' if topic else ''}{option_text}"

    return {
        "content": blank_content,
        "answer": answer,
        "explanation": explanation[:150],
    }


def process_year_file(year_file: Path, sid: str) -> list[dict]:
    """Process a year quiz file and generate blanks."""
    with open(year_file, encoding="utf-8") as f:
        questions = json.load(f)

    mc_questions = [q for q in questions if q["type"] == "multiple_choice"]
    blanks = []

    for i, mc_q in enumerate(mc_questions):
        result = create_blank_from_mc(mc_q)
        if result is None:
            continue

        year_str = year_file.stem.split("_")[0]  # "y2024"
        blank_id = f"{sid}_{year_str}_b{i+1:04d}"

        blanks.append(
            {
                "id": blank_id,
                "type": "fill_in_the_blank",
                **result,
            }
        )

    return blanks


def process_subject(quiz_dir: Path, sid: str) -> int:
    """Process all year files for a subject. Returns number of blanks generated."""
    subj_dir = quiz_dir / sid
    if not subj_dir.exists():
        return 0

    # Match y2021_quiz.json etc but NOT year_2021_quiz.json (old format)
    year_files = sorted(
        f for f in subj_dir.glob("y*_quiz.json") if not f.stem.startswith("year_")
    )
    if not year_files:
        print(f"  {sid}: no year quiz files found")
        return 0

    total_blanks = 0
    all_questions = []

    for year_file in year_files:
        with open(year_file, encoding="utf-8") as f:
            mc_questions = json.load(f)

        # Only keep MC questions (remove any old blanks)
        mc_only = [q for q in mc_questions if q["type"] == "multiple_choice"]

        blanks = process_year_file(year_file, sid)
        total_blanks += len(blanks)

        year_str = year_file.stem.split("_")[0]
        print(f"  {year_str}: {len(mc_only)} MC → {len(blanks)} blanks")

        # Write updated year file (MC + new blanks)
        combined = mc_only + blanks
        year_file.write_text(
            json.dumps(combined, ensure_ascii=False, indent=2), encoding="utf-8"
        )

        all_questions.extend(combined)

    # Rebuild all_quiz.json
    all_path = subj_dir / "all_quiz.json"
    all_path.write_text(
        json.dumps(all_questions, ensure_ascii=False, indent=2), encoding="utf-8"
    )

    return total_blanks


def copy_to_frontend(quiz_dir: Path) -> None:
    """Copy quiz data to frontend public/data/realtor/."""
    frontend_dir = Path(__file__).parent.parent / "public" / "data" / "realtor"
    frontend_dir.mkdir(parents=True, exist_ok=True)

    for sid in ["s1", "s2", "s3", "s4", "s5", "s6"]:
        src = quiz_dir / sid
        if not src.exists():
            continue
        dst = frontend_dir / sid
        dst.mkdir(exist_ok=True)

        for json_file in src.glob("*.json"):
            if json_file.stem.startswith("year_"):
                continue
            (dst / json_file.name).write_text(
                json_file.read_text(encoding="utf-8"), encoding="utf-8"
            )
        print(f"  Copied {sid}/")

    curr_src = quiz_dir / "curriculum.json"
    if curr_src.exists():
        (frontend_dir / "curriculum.json").write_text(
            curr_src.read_text(encoding="utf-8"), encoding="utf-8"
        )
        print("  Copied curriculum.json")


def main():
    parser = argparse.ArgumentParser(
        description="Generate fill-in-the-blank questions from MC data"
    )
    parser.add_argument("--subject", "-s", help="Process single subject (e.g., s1)")
    parser.add_argument(
        "--copy-to-frontend",
        action="store_true",
        help="Copy output to public/data/",
    )
    parser.add_argument(
        "--dry-run", action="store_true", help="Show stats without generating"
    )
    args = parser.parse_args()

    quiz_dir = Path("output/quiz")
    subjects = (
        [args.subject] if args.subject else ["s1", "s2", "s3", "s4", "s5", "s6"]
    )

    if args.dry_run:
        total_mc = 0
        total_eligible = 0
        for sid in subjects:
            all_path = quiz_dir / sid / "all_quiz.json"
            if not all_path.exists():
                continue
            data = json.load(open(all_path, encoding="utf-8"))
            mc = [q for q in data if q["type"] == "multiple_choice"]
            eligible = [
                q
                for q in mc
                if not is_wrong_answer_question(q["content"])
                and not is_skip_option(q["options"][q["correctIndex"]])
            ]
            print(f"{sid}: {len(mc)} MC, {len(eligible)} eligible for blanks")
            total_mc += len(mc)
            total_eligible += len(eligible)
        print(f"\nTotal: {total_mc} MC, {total_eligible} eligible")
        return

    total = 0
    for sid in subjects:
        print(f"\n{sid}:")
        count = process_subject(quiz_dir, sid)
        total += count

    print(f"\nTotal fill-in-the-blank questions generated: {total}")

    if args.copy_to_frontend:
        print("\nCopying to frontend...")
        copy_to_frontend(quiz_dir)

    print("Done!")


if __name__ == "__main__":
    main()
