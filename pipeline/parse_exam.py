"""
PDF 기출문제 파서 — PDF에서 개별 문제를 추출하고 정답을 매칭합니다.

Usage:
    python parse_exam.py data/기출문제/  --output output/parsed/
    python parse_exam.py data/기출문제/2024년*.pdf --output output/parsed/
"""

import argparse
import json
import re
import sys
import unicodedata
from pathlib import Path

import pdfplumber


# ── Subject mapping ──────────────────────────────────────────
# 1차: 1교시 → 부동산학개론(Q1-40) + 민법(Q41-80)
# 2차: 1교시 → 공인중개사법(Q1-40) + 부동산공법(Q41-80)
# 2차: 2교시 → 부동산공시법(Q1-40) + 부동산세법(Q41-80)

SUBJECT_MAP = {
    ("1차", "1교시", 1): {"id": "s1", "name": "부동산학개론", "q_range": (1, 40)},
    ("1차", "1교시", 2): {"id": "s2", "name": "민법 및 민사특별법", "q_range": (41, 80)},
    ("2차", "1교시", 1): {"id": "s5", "name": "공인중개사법령 및 중개실무", "q_range": (1, 40)},
    ("2차", "1교시", 2): {"id": "s3", "name": "부동산공법", "q_range": (41, 80)},
    ("2차", "2교시", 1): {"id": "s4", "name": "부동산공시법령", "q_range": (1, 40)},
    ("2차", "2교시", 2): {"id": "s6", "name": "부동산세법", "q_range": (41, 80)},
}

# lek file mapping: lek_XX → subject id
LEK_SUBJECT_MAP = {
    "01": {"id": "s1", "name": "부동산학개론"},
    "02": {"id": "s2", "name": "민법 및 민사특별법"},
    "03": {"id": "s5", "name": "공인중개사법령 및 중개실무"},
    "04": {"id": "s3", "name": "부동산공법"},
    "05": {"id": "s4", "name": "부동산공시법령"},
    "06": {"id": "s6", "name": "부동산세법"},
}


def extract_text_from_pdf(pdf_path: str) -> str:
    """Extract text from a PDF, handling 2-column layouts."""
    full_text = ""
    with pdfplumber.open(pdf_path) as pdf:
        for page in pdf.pages:
            w = page.width
            h = page.height

            # Try column extraction: split page in half
            left = page.crop((0, 0, w / 2, h))
            right = page.crop((w / 2, 0, w, h))

            left_text = left.extract_text() or ""
            right_text = right.extract_text() or ""

            # If single-column (answer sheets), just use full page
            if not right_text.strip() or len(right_text.strip()) < 50:
                full_text += (page.extract_text() or "") + "\n"
            else:
                full_text += left_text + "\n" + right_text + "\n"

            full_text += "\n--- PAGE BREAK ---\n"

    return unicodedata.normalize("NFC", full_text)


def _clean_answer_line(line: str) -> str:
    """Pre-process an answer line to normalize spacing and special cases.

    Handles:
    - "전항 정답" / "전항정답" → "0" (placeholder for unchanged answer)
    - "3, 5" (space after comma) → "3,5" (join multi-answer)
    - "1,2,3,4,5" → "1" (take first of multi-answer)
    """
    # Remove "전항 정답" / "전항정답" variants → replace with 0
    line = re.sub(r"전항\s*정답", "0", line)
    # Join "N, M" → "N,M" (remove space after comma between digits)
    line = re.sub(r"(\d),\s+(\d)", r"\1,\2", line)
    return line


def parse_answer_key(pdf_path: str) -> dict[str, dict[int, int]]:
    """Parse answer key PDF. Returns {subject_name: {q_num: answer}}.

    Multi-answer entries like "2,4" are stored as the first valid answer.
    """
    answers: dict[str, dict[int, int]] = {}
    current_subject = None

    with pdfplumber.open(pdf_path) as pdf:
        for page in pdf.pages:
            text = unicodedata.normalize("NFC", page.extract_text() or "")
            lines = text.strip().split("\n")

            i = 0
            while i < len(lines):
                line = lines[i].strip()

                # Detect subject header: ■ 부동산학개론  or ■ 부동산학개론(A)
                if line.startswith("■"):
                    current_subject = line.replace("■", "").strip()
                    answers.setdefault(current_subject, {})
                    i += 1
                    continue

                # Parse question-answer pairs from table rows
                if current_subject and re.match(r"^\d+", line):
                    q_line = _clean_answer_line(line)
                    q_tokens = q_line.split()
                    # Extract question numbers (must be sequential integers)
                    try:
                        q_nums = [int(t) for t in q_tokens]
                    except ValueError:
                        i += 1
                        continue

                    # Validate they look like question numbers (sequential)
                    if len(q_nums) >= 2 and q_nums[0] < q_nums[-1]:
                        # Check if next line has the answers
                        if i + 1 < len(lines):
                            next_line = _clean_answer_line(lines[i + 1].strip())
                            a_tokens = next_line.split()
                            if len(a_tokens) == len(q_nums):
                                try:
                                    for q_str, a_str in zip(q_tokens, a_tokens):
                                        q_num = int(q_str)
                                        # Handle multi-answer: "2,4" → take first digit
                                        first_ans = re.match(r"\d+", a_str)
                                        if first_ans:
                                            answers[current_subject][q_num] = int(first_ans.group())
                                    i += 2
                                    continue
                                except ValueError:
                                    pass
                i += 1

    return answers


def parse_questions_from_text(text: str) -> list[dict]:
    """Parse individual questions from extracted exam text."""
    questions = []

    # Pattern: number followed by period at line start
    # e.g., "1. 토지의 특성에 관한..."
    q_pattern = re.compile(r"^(\d{1,2})\.\s+(.+?)(?=^\d{1,2}\.\s|\Z)", re.MULTILINE | re.DOTALL)

    matches = list(q_pattern.finditer(text))

    for match in matches:
        q_num = int(match.group(1))
        q_body = match.group(2).strip()

        # Remove page break artifacts
        q_body = re.sub(r"---\s*PAGE BREAK\s*---", "", q_body)
        q_body = re.sub(r"\d{4}년\s+제\d+회\s+공인중개사.*?A형.*?\d+-\d+", "", q_body)

        # Extract options (①②③④⑤)
        option_pattern = re.compile(r"([①②③④⑤])\s*(.+?)(?=[①②③④⑤]|\Z)", re.DOTALL)
        option_matches = list(option_pattern.finditer(q_body))

        options = []
        content = q_body

        if option_matches:
            # Content is everything before first option
            content = q_body[: option_matches[0].start()].strip()

            for om in option_matches:
                opt_text = om.group(2).strip()
                # Clean up multiline options
                opt_text = re.sub(r"\s+", " ", opt_text).strip()
                options.append(opt_text)

        # Clean content
        content = re.sub(r"\s+", " ", content).strip()

        # Skip if no meaningful content
        if len(content) < 5:
            continue

        questions.append({
            "number": q_num,
            "content": content,
            "options": options,
        })

    return questions



# ── Manual overrides for files whose names don't contain a parseable year ──
MANUAL_FILE_MAP = {
    # 2016 제27회 (업로드일 2017년이라 자동감지 실패)
    "공인중개사-1차 A형20170427181542": {"year": 2016, "round": 27},
    "공인중개사-1차 B형20170427181613": {"year": 2016, "round": 27},
    "공인중개사-2차 A형20170427181630": {"year": 2016, "round": 27},
    "공인중개사-2차 B형20170427181644": {"year": 2016, "round": 27},
    # 2017 제28회 시험지
    "1차 1교시(A형)20171213100952": {"year": 2017, "round": 28},
    "1차 1교시(B형)20171213100939": {"year": 2017, "round": 28},
    "2차 1교시(A형)20171213100925": {"year": 2017, "round": 28},
    "2차 1교시(B형)20171213100900": {"year": 2017, "round": 28},
    "2차 2교시(A형)20171213100832": {"year": 2017, "round": 28},
    "2차 2교시(B형)20171213100816": {"year": 2017, "round": 28},
    # 2017 제28회 통합본 (중복 시험지 → 스킵)
    "공인A형_1차(학개론&민법)20171129093529": {"year": 2017, "round": 28, "file_type": "duplicate"},
    "공인A형_2차(중개사법,공법,공시세법)20171129093457": {"year": 2017, "round": 28, "file_type": "duplicate"},
    "공인B형_1차(학개론&민법)20171129093513": {"year": 2017, "round": 28, "file_type": "duplicate"},
    "공인B형_2차(중개사법,공법,공시세법)20171129093422": {"year": 2017, "round": 28, "file_type": "duplicate"},
    # 2025 정답지 (파일명에 "년" 없음)
    "251025_공인_풀서비스_가답안(산인공)_1차20251027133628": {"year": 2025, "round": 36},
    "251025_공인_풀서비스_가답안(산인공)_ 2차20251027133702": {"year": 2025, "round": 36},
}

def classify_exam_file(filename: str) -> dict:
    """Classify a PDF file by exam type, year, session."""
    name = unicodedata.normalize("NFC", Path(filename).stem)

    info = {
        "year": None,
        "round": None,  # 회차
        "exam_type": None,  # 1차/2차
        "session": None,  # 교시
        "form": None,  # A형/B형
        "file_type": None,  # exam/answer/explanation/duplicate
    }

    # Check manual override first
    manual = MANUAL_FILE_MAP.get(name)
    if manual:
        info["year"] = manual["year"]
        info["round"] = manual["round"]
        if "file_type" in manual:
            info["file_type"] = manual["file_type"]
            # For duplicates, still extract exam_type/form for reference
            if manual["file_type"] == "duplicate":
                if "1차" in name:
                    info["exam_type"] = "1차"
                elif "2차" in name:
                    info["exam_type"] = "2차"
                if "A형" in name:
                    info["form"] = "A"
                elif "B형" in name:
                    info["form"] = "B"
                return info

    # Extract year
    year_match = re.search(r"(20\d{2})년|(\d{2})년", name)
    if year_match and info["year"] is None:
        info["year"] = int(year_match.group(1) or f"20{year_match.group(2)}")

    # Extract round (회차)
    round_match = re.search(r"제?(\d{1,2})회", name)
    if round_match and info["round"] is None:
        info["round"] = int(round_match.group(1))

    # Derive year from round if year not found (제N회 → year = N + 1989)
    if info["year"] is None and info["round"]:
        info["year"] = info["round"] + 1989

    # Check if answer key
    if info["file_type"] is None:
        if any(kw in name for kw in ["정답", "답안", "가답안"]):
            info["file_type"] = "answer"
        elif "해설" in name:
            info["file_type"] = "explanation"
        elif "대비" in name:
            info["file_type"] = "prep"
        else:
            info["file_type"] = "exam"

    # Extract exam type and session
    if "1차" in name:
        info["exam_type"] = "1차"
        info["session"] = "1교시"
    elif "2차" in name:
        info["exam_type"] = "2차"
        if "2교시" in name:
            info["session"] = "2교시"
        else:
            info["session"] = "1교시"

    # Extract form type
    if "A형" in name or "(A형)" in name or "A형" in name:
        info["form"] = "A"
    elif "B형" in name or "(B형)" in name:
        info["form"] = "B"

    # Handle lek files: lek_XX_YY
    lek_match = re.match(r"lek_(\d{2})_(\d{2})", name)
    if lek_match:
        subj_code = lek_match.group(1)
        year_suffix = lek_match.group(2)
        info["year"] = 2000 + int(year_suffix)
        info["file_type"] = "exam"
        info["lek_subject"] = subj_code
        # lek_01-02 = 1차, lek_03-06 = 2차
        if subj_code in ("01", "02"):
            info["exam_type"] = "1차"
            info["session"] = "1교시"
        elif subj_code in ("03", "04"):
            info["exam_type"] = "2차"
            info["session"] = "1교시"
        elif subj_code in ("05", "06"):
            info["exam_type"] = "2차"
            info["session"] = "2교시"

    return info


def detect_subjects_in_text(text: str) -> list[dict]:
    """Detect subject boundaries in extracted text."""
    text = unicodedata.normalize("NFC", text)
    subjects = []
    # Pattern: 제N과목 : 과목명
    subj_pattern = re.compile(r"제(\d)과목\s*[:\：]\s*(.+?)(?:\n|$)")
    matches = list(subj_pattern.finditer(text))

    for i, m in enumerate(matches):
        subj_num = int(m.group(1))
        subj_name = m.group(2).strip()
        start = m.start()
        end = matches[i + 1].start() if i + 1 < len(matches) else len(text)
        subjects.append({
            "number": subj_num,
            "name": subj_name,
            "start": start,
            "end": end,
        })

    return subjects


def match_subject_id(subj_name: str) -> str | None:
    """Match a detected subject name to a subject ID."""
    name = unicodedata.normalize("NFC", subj_name)
    # Order matters: check more specific patterns first
    patterns = [
        ("부동산학개론", "s1"),
        ("민법", "s2"),
        ("공인중개사", "s5"),
        ("중개사법", "s5"),
        ("중개실무", "s5"),
        ("부동산공법", "s3"),
        ("부동산공시", "s4"),
        ("공시법", "s4"),
        ("공간정보", "s4"),
        ("부동산세법", "s6"),
        ("세법", "s6"),
    ]
    for key, sid in patterns:
        if key in name:
            return sid
    return None


def process_exam_pdf(
    pdf_path: str,
    answer_map: dict[str, dict[int, int]] | None = None,
) -> list[dict]:
    """Process a single exam PDF and return structured questions."""
    file_info = classify_exam_file(pdf_path)

    if file_info["file_type"] != "exam":
        return []

    print(f"  Extracting text from: {Path(pdf_path).name}")
    text = extract_text_from_pdf(pdf_path)

    # Detect subjects in text
    subjects = detect_subjects_in_text(text)

    all_questions = []

    # Session-based subject mapping for splitting by question number
    SESSION_SPLIT = {
        ("1차", "1교시"): [
            {"id": "s1", "name": "부동산학개론", "range": (1, 40)},
            {"id": "s2", "name": "민법 및 민사특별법", "range": (41, 80)},
        ],
        ("2차", "1교시"): [
            {"id": "s5", "name": "공인중개사법령 및 중개실무", "range": (1, 40)},
            {"id": "s3", "name": "부동산공법", "range": (41, 80)},
        ],
        ("2차", "2교시"): [
            {"id": "s4s6", "name": "부동산공시법령 및 부동산세법", "range": (1, 40)},
        ],
    }

    if subjects and len(subjects) >= 2:
        # Multi-subject PDF with clear headers
        for subj in subjects:
            subj_text = text[subj["start"] : subj["end"]]
            subj_id = match_subject_id(subj["name"])
            questions = parse_questions_from_text(subj_text)

            for q in questions:
                q["subject_id"] = subj_id
                q["subject_name"] = subj["name"]
                q["year"] = file_info["year"]
                q["round"] = file_info["round"]
                _match_answer(q, answer_map, subj["name"])
                all_questions.append(q)

    elif file_info.get("lek_subject"):
        # Single-subject lek files
        lek_info = LEK_SUBJECT_MAP.get(file_info["lek_subject"])
        if lek_info:
            questions = parse_questions_from_text(text)
            for q in questions:
                q["subject_id"] = lek_info["id"]
                q["subject_name"] = lek_info["name"]
                q["year"] = file_info["year"]
                q["round"] = file_info.get("round")
            all_questions.extend(questions)

    elif file_info.get("exam_type") and file_info.get("session"):
        # Use session info to split by question number
        session_key = (file_info["exam_type"], file_info["session"])
        split_info = SESSION_SPLIT.get(session_key)

        questions = parse_questions_from_text(text)

        if split_info:
            for q in questions:
                q["year"] = file_info["year"]
                q["round"] = file_info.get("round")
                # Assign subject based on question number
                for si in split_info:
                    lo, hi = si["range"]
                    if lo <= q["number"] <= hi:
                        q["subject_id"] = si["id"]
                        q["subject_name"] = si["name"]
                        _match_answer(q, answer_map, si["name"])
                        break
                all_questions.append(q)
        else:
            for q in questions:
                q["year"] = file_info["year"]
                q["round"] = file_info.get("round")
            all_questions.extend(questions)

    else:
        # Fallback: try to parse without subject detection
        questions = parse_questions_from_text(text)
        for q in questions:
            q["year"] = file_info["year"]
            q["round"] = file_info.get("round")
        all_questions.extend(questions)

    print(f"    → Parsed {len(all_questions)} questions")
    return all_questions


# Map subject_id to patterns for answer key matching.
# Order within each list matters for disambiguation.
_ANSWER_KEY_PATTERNS: dict[str, list[str]] = {
    "s1": ["부동산학개론", "학개론"],
    "s2": ["민법"],
    "s3": ["부동산공법"],
    "s4": ["부동산공시법"],
    "s4s6": ["공시법", "세법"],
    "s5": ["중개사법", "중개실무", "공인중개사"],
    "s6": ["부동산세법"],
}

# Subject IDs that should NOT match certain answer key names
_ANSWER_KEY_EXCLUSIONS: dict[str, list[str]] = {
    "s4": ["세법"],  # s4 should not match "공시법 및 세법" (that's s4s6)
}


def _match_answer(
    q: dict,
    answer_map: dict[str, dict[int, int]] | None,
    subj_name: str,
) -> None:
    """Try to match answer from answer_map into the question dict."""
    if not answer_map:
        return

    sid = q.get("subject_id")
    if not sid:
        return
    patterns = _ANSWER_KEY_PATTERNS.get(sid, [])
    exclusions = _ANSWER_KEY_EXCLUSIONS.get(sid, [])

    for ans_name in answer_map:
        # Strip form suffix like "(A)", "(B)" and normalize
        nfc_ans = unicodedata.normalize("NFC", ans_name)
        clean_ans = re.sub(r"\([A-Z]\)", "", nfc_ans).strip()

        # Check exclusions first
        if any(ex in clean_ans for ex in exclusions):
            continue

        for pat in patterns:
            if pat in clean_ans:
                q_num = q["number"]
                if q_num in answer_map[ans_name]:
                    q["answer"] = answer_map[ans_name][q_num]
                return


def find_answer_file(exam_file: str, all_files: list[str]) -> str | None:
    """Find the matching answer key file for an exam file."""
    info = classify_exam_file(exam_file)
    if not info["year"]:
        return None

    candidates = []
    for f in all_files:
        f_info = classify_exam_file(f)
        if f_info["file_type"] != "answer":
            continue
        if f_info["year"] != info["year"]:
            continue
        candidates.append((f, f_info))

    if not candidates:
        return None

    # Pass 1: exact match (same exam type + same form)
    for f, f_info in candidates:
        if info["exam_type"] and f_info["exam_type"] == info["exam_type"]:
            if info["form"] and f_info["form"] and info["form"] == f_info["form"]:
                return f

    # Pass 2: same exam type, prefer A형 or no-form
    for f, f_info in candidates:
        if info["exam_type"] and f_info["exam_type"] == info["exam_type"]:
            if f_info["form"] in (None, "A"):
                return f

    # Pass 3: same exam type, any form
    for f, f_info in candidates:
        if info["exam_type"] and f_info["exam_type"] == info["exam_type"]:
            return f

    # Pass 4: generic answer file (covers all exam types, e.g. 제25회)
    for f, f_info in candidates:
        if not f_info["exam_type"]:
            return f

    return None


def process_directory(input_dir: str, output_dir: str) -> None:
    """Process all exam PDFs in a directory."""
    input_path = Path(input_dir)
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    # Collect all PDF files
    pdf_files = sorted(input_path.glob("*.pdf"))
    if not pdf_files:
        print(f"No PDF files found in {input_dir}")
        sys.exit(1)

    all_file_strs = [str(f) for f in pdf_files]

    # Classify files
    exam_files = []
    answer_files = []
    skipped = []

    for f in pdf_files:
        info = classify_exam_file(str(f))
        if info["file_type"] == "duplicate":
            skipped.append(f.name)
            continue
        if info["file_type"] == "exam":
            # Skip B형 duplicates (prefer A형)
            if info["form"] == "B":
                skipped.append(f.name)
                continue
            # Skip duplicate files (files with "(1)" in name)
            if "(1)" in f.name:
                skipped.append(f.name)
                continue
            exam_files.append(str(f))
        elif info["file_type"] == "answer":
            answer_files.append(str(f))
        else:
            skipped.append(f.name)

    print(f"Found {len(exam_files)} exam files, {len(answer_files)} answer files")
    print(f"Skipped {len(skipped)} files (B형 duplicates, explanations, etc.)")

    # Process each exam file
    all_questions: list[dict] = []
    by_subject: dict[str, list[dict]] = {}

    for exam_file in exam_files:
        print(f"\nProcessing: {Path(exam_file).name}")

        try:
            # Find matching answer key
            answer_file = find_answer_file(exam_file, all_file_strs)
            answer_map = None
            if answer_file:
                print(f"  Answer key: {Path(answer_file).name}")
                try:
                    answer_map = parse_answer_key(answer_file)
                except Exception as e:
                    print(f"  ⚠ Answer parse error: {e}")

            questions = process_exam_pdf(exam_file, answer_map)
            all_questions.extend(questions)

            for q in questions:
                sid = q.get("subject_id", "unknown")
                by_subject.setdefault(sid, []).append(q)
        except Exception as e:
            print(f"  ⚠ Error processing: {e}")

    # Write combined output
    combined_path = output_path / "all_questions.json"
    combined_path.write_text(
        json.dumps(all_questions, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    print(f"\n{'='*60}")
    print(f"Total questions parsed: {len(all_questions)}")
    print(f"Saved combined output: {combined_path}")

    # Write per-subject output
    for sid, qs in sorted(by_subject.items(), key=lambda x: x[0] or "zzz"):
        subj_name = qs[0].get("subject_name", sid) if qs else sid
        safe_name = re.sub(r"[^\w가-힣]", "_", sid or "unknown")
        subj_path = output_path / f"{safe_name}_questions.json"
        subj_path.write_text(
            json.dumps(qs, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        print(f"  {subj_name}: {len(qs)} questions → {subj_path.name}")

    # Summary stats
    print(f"\n{'='*60}")
    print("Subject breakdown:")
    for sid, qs in sorted(by_subject.items(), key=lambda x: x[0] or "zzz"):
        subj_name = qs[0].get("subject_name", sid) if qs else sid
        years = sorted({q["year"] for q in qs if q.get("year")})
        with_answer = sum(1 for q in qs if q.get("answer"))
        print(f"  {subj_name}: {len(qs)} questions, {with_answer} with answers, years: {min(years) if years else '?'}-{max(years) if years else '?'}")


def main():
    parser = argparse.ArgumentParser(description="Parse exam PDFs into structured questions")
    parser.add_argument("input", help="Input directory containing PDF files")
    parser.add_argument("--output", "-o", default="output/parsed", help="Output directory")
    args = parser.parse_args()

    process_directory(args.input, args.output)


if __name__ == "__main__":
    main()
