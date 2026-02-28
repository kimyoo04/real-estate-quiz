"""
Build frontend quiz JSON from parsed exam questions.

Phase 1: Direct conversion (no LLM needed)
- Converts parsed questions with answers to MultipleChoice format
- Organizes by subject
- Generates curriculum.json from tree structure

Phase 2: LLM-enhanced (requires OpenAI API key)
- Classifies questions into tree nodes (chapters)
- Generates explanations
- Creates fill-in-the-blank versions

Usage:
    python build_quiz.py                     # Phase 1 only
    python build_quiz.py --with-ai           # Phase 1 + Phase 2
    python build_quiz.py --subject s1        # Process single subject
"""

import argparse
import json
import sys
from pathlib import Path

# ── Tree structure (matching src/data/examTree.ts) ─────────────────
# Subject ID → { name, examType, chapters: [{id, name}] }
SUBJECTS = {
    "s1": {
        "name": "부동산학개론",
        "examType": "first",
        "chapters": [
            {"id": "s1-m1", "name": "부동산학 총론"},
            {"id": "s1-m2", "name": "부동산 경제론"},
            {"id": "s1-m3", "name": "부동산 정책론"},
            {"id": "s1-m4", "name": "부동산 투자론"},
            {"id": "s1-m5", "name": "부동산 개발·관리론"},
            {"id": "s1-m6", "name": "부동산 감정평가론"},
        ],
    },
    "s2": {
        "name": "민법 및 민사특별법",
        "examType": "first",
        "chapters": [
            {"id": "s2-m1", "name": "민법총칙"},
            {"id": "s2-m2", "name": "물권법"},
            {"id": "s2-m3", "name": "채권법"},
            {"id": "s2-m4", "name": "민사특별법"},
        ],
    },
    "s3": {
        "name": "부동산공법",
        "examType": "second",
        "chapters": [
            {"id": "s3-m1", "name": "국토의 계획 및 이용에 관한 법률"},
            {"id": "s3-m2", "name": "도시개발법"},
            {"id": "s3-m3", "name": "도시 및 주거환경정비법"},
            {"id": "s3-m4", "name": "건축법"},
            {"id": "s3-m5", "name": "주택법"},
            {"id": "s3-m6", "name": "농지법"},
        ],
    },
    "s4": {
        "name": "부동산공시법령",
        "examType": "second",
        "chapters": [
            {"id": "s4-m1", "name": "부동산등기법"},
            {"id": "s4-m2", "name": "공간정보의 구축 및 관리 등에 관한 법률"},
            {"id": "s4-m3", "name": "부동산 가격공시에 관한 법률"},
        ],
    },
    "s5": {
        "name": "공인중개사법령 및 중개실무",
        "examType": "second",
        "chapters": [
            {"id": "s5-m1", "name": "공인중개사법"},
            {"id": "s5-m2", "name": "중개실무"},
            {"id": "s5-m3", "name": "부동산 거래신고 등에 관한 법률"},
        ],
    },
    "s6": {
        "name": "부동산세법",
        "examType": "second",
        "chapters": [
            {"id": "s6-m1", "name": "조세총론"},
            {"id": "s6-m2", "name": "취득세"},
            {"id": "s6-m3", "name": "등록면허세"},
            {"id": "s6-m4", "name": "재산세"},
            {"id": "s6-m5", "name": "종합부동산세"},
            {"id": "s6-m6", "name": "양도소득세"},
            {"id": "s6-m7", "name": "부가가치세 (부동산 관련)"},
            {"id": "s6-m8", "name": "기타 세목"},
        ],
    },
}

# Combined s4s6 subject maps to s4 + s6 chapters
COMBINED_SUBJECTS = {
    "s4s6": {"maps_to": ["s4", "s6"], "name": "부동산공시법령 및 부동산세법"},
}


def load_parsed_questions(input_dir: str) -> list[dict]:
    """Load all parsed questions from JSON."""
    path = Path(input_dir) / "all_questions.json"
    if not path.exists():
        print(f"Error: {path} not found. Run parse_exam.py first.", file=sys.stderr)
        sys.exit(1)
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def convert_to_frontend_format(questions: list[dict], subject_id: str) -> list[dict]:
    """Convert parsed questions to frontend MultipleChoice format.

    Only includes questions that have a correct answer.
    """
    result = []
    idx = 1

    for q in questions:
        if not q.get("answer"):
            continue
        if len(q.get("options", [])) < 2:
            continue

        correct_index = q["answer"] - 1  # Convert 1-based to 0-based
        if correct_index < 0 or correct_index >= len(q["options"]):
            continue

        result.append({
            "id": f"{subject_id}_q{idx:04d}",
            "type": "multiple_choice",
            "year": q.get("year", 0),
            "content": q["content"],
            "options": q["options"],
            "correctIndex": correct_index,
            "explanation": "",  # Will be filled by LLM in Phase 2
        })
        idx += 1

    return result


def build_curriculum(by_subject: dict[str, list[dict]]) -> dict:
    """Build curriculum.json with year-based chapters from actual data."""
    subjects = []
    for sid, info in SUBJECTS.items():
        qs = by_subject.get(sid, [])
        answered_qs = [q for q in qs if q.get("answer")]
        years = sorted({q.get("year") for q in answered_qs if q.get("year")}, reverse=True)

        if not years:
            continue

        chapters = []
        # "All questions" chapter
        chapters.append({
            "id": "all",
            "name": f"전체 기출문제 ({len(answered_qs)}문제)",
        })
        # Per-year chapters
        for year in years:
            year_count = sum(1 for q in answered_qs if q.get("year") == year)
            chapters.append({
                "id": f"y{year}",
                "name": f"{year}년 기출 ({year_count}문제)",
            })

        subjects.append({
            "id": sid,
            "name": info["name"],
            "chapters": chapters,
        })

    return {
        "examId": "realtor",
        "subjects": subjects,
    }


def build_phase1(input_dir: str, output_dir: str, subject_filter: str | None = None) -> None:
    """Phase 1: Direct conversion without LLM."""
    all_questions = load_parsed_questions(input_dir)
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    # Group questions by subject_id
    by_subject: dict[str, list[dict]] = {}
    for q in all_questions:
        sid = q.get("subject_id")
        if sid:
            by_subject.setdefault(sid, []).append(q)

    # Handle s4s6 combined subject — split into s4 and s6 by question number
    # In the 2차 2교시, questions 1-20 are 공시법, 21-40 are 세법
    if "s4s6" in by_subject:
        s4s6_qs = by_subject.pop("s4s6")
        for q in s4s6_qs:
            if q["number"] <= 20:
                q["subject_id"] = "s4"
                by_subject.setdefault("s4", []).append(q)
            else:
                q["subject_id"] = "s6"
                by_subject.setdefault("s6", []).append(q)

    # Write curriculum.json (needs by_subject data for counts)
    curriculum = build_curriculum(by_subject)
    curriculum_path = output_path / "curriculum.json"
    curriculum_path.write_text(
        json.dumps(curriculum, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    print(f"Wrote {curriculum_path}")

    # Process each subject
    total_quiz = 0
    for sid, info in SUBJECTS.items():
        if subject_filter and sid != subject_filter:
            continue

        qs = by_subject.get(sid, [])
        frontend_qs = convert_to_frontend_format(qs, sid)

        if not frontend_qs:
            print(f"  {sid} ({info['name']}): no questions with answers, skipping")
            continue

        # Sort by year descending, then by question number
        frontend_qs.sort(key=lambda x: (-x["year"], x["id"]))

        # Write per-subject quiz file
        subj_dir = output_path / sid
        subj_dir.mkdir(exist_ok=True)

        # Write "all" chapter quiz file (matches curriculum chapter id "all")
        all_path = subj_dir / "all_quiz.json"
        all_path.write_text(
            json.dumps(frontend_qs, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )

        # Write per-year chapter files (matches curriculum chapter id "yYYYY")
        by_year: dict[int, list[dict]] = {}
        for q in frontend_qs:
            by_year.setdefault(q["year"], []).append(q)

        for year, year_qs in sorted(by_year.items()):
            year_path = subj_dir / f"y{year}_quiz.json"
            year_path.write_text(
                json.dumps(year_qs, ensure_ascii=False, indent=2),
                encoding="utf-8",
            )

        total_quiz += len(frontend_qs)
        years = sorted(by_year.keys())
        print(f"  {sid} ({info['name']}): {len(frontend_qs)} questions, years: {min(years)}-{max(years)}")

    print(f"\nTotal quiz questions generated: {total_quiz}")


def build_phase2_classify(
    input_dir: str,
    output_dir: str,
    model_name: str = "gpt-4o-mini",
    subject_filter: str | None = None,
) -> None:
    """Phase 2: LLM-based classification and enhancement."""
    try:
        from dotenv import load_dotenv
        from langchain_core.prompts import ChatPromptTemplate
        from langchain_openai import ChatOpenAI

        load_dotenv()
    except ImportError:
        print("Error: langchain/openai packages required for Phase 2.", file=sys.stderr)
        print("Run: pip install langchain langchain-openai python-dotenv", file=sys.stderr)
        sys.exit(1)

    output_path = Path(output_dir)

    for sid, info in SUBJECTS.items():
        if subject_filter and sid != subject_filter:
            continue

        subj_dir = output_path / sid
        quiz_file = subj_dir / "all_quiz.json"
        if not quiz_file.exists():
            continue

        with open(quiz_file, encoding="utf-8") as f:
            questions = json.load(f)

        if not questions:
            continue

        chapters = info["chapters"]
        chapter_list = "\n".join(f"- {ch['id']}: {ch['name']}" for ch in chapters)

        print(f"\n  Classifying {sid} ({info['name']}): {len(questions)} questions")

        # Batch classify
        llm = ChatOpenAI(model=model_name, temperature=0)

        classify_prompt = ChatPromptTemplate.from_messages([
            ("system", """\
당신은 한국 공인중개사 시험 전문가입니다.
주어진 문제들을 아래 단원 목록에서 가장 적합한 단원으로 분류하세요.

단원 목록:
{chapters}

각 문제에 대해 다음 JSON 형식으로 응답하세요:
{{"classifications": [{{"question_id": "...", "chapter_id": "..."}}]}}
"""),
            ("human", "다음 문제들을 분류해주세요:\n\n{questions_text}"),
        ])

        explain_prompt = ChatPromptTemplate.from_messages([
            ("system", """\
당신은 한국 공인중개사 시험 전문가입니다.
주어진 기출문제의 정답에 대한 간결한 해설을 작성하세요.
해설은 1-2문장으로, 왜 그 답이 정답인지 설명합니다.
JSON 형식으로 응답: {{"explanations": [{{"question_id": "...", "explanation": "..."}}]}}
"""),
            ("human", "다음 문제들의 해설을 작성해주세요:\n\n{questions_text}"),
        ])

        BATCH_SIZE = 10
        classified = {}
        explained = {}

        for i in range(0, len(questions), BATCH_SIZE):
            batch = questions[i : i + BATCH_SIZE]
            batch_text = ""
            for q in batch:
                correct = q["options"][q["correctIndex"]] if q["options"] else ""
                batch_text += f"\nID: {q['id']}\n문제: {q['content']}\n정답: {correct}\n"

            # Classify
            try:
                result = llm.invoke(
                    classify_prompt.format_messages(
                        chapters=chapter_list, questions_text=batch_text
                    )
                )
                data = json.loads(result.content)
                for c in data.get("classifications", []):
                    classified[c["question_id"]] = c["chapter_id"]
            except Exception as e:
                print(f"    Classification error at batch {i}: {e}")

            # Explain
            try:
                result = llm.invoke(
                    explain_prompt.format_messages(questions_text=batch_text)
                )
                data = json.loads(result.content)
                for e_item in data.get("explanations", []):
                    explained[e_item["question_id"]] = e_item["explanation"]
            except Exception as e:
                print(f"    Explanation error at batch {i}: {e}")

            done = min(i + BATCH_SIZE, len(questions))
            print(f"    Processed {done}/{len(questions)}", end="\r")

        print(f"    Classified: {len(classified)}, Explained: {len(explained)}")

        # Apply classifications and explanations
        by_chapter: dict[str, list[dict]] = {}
        unclassified = []

        for q in questions:
            ch_id = classified.get(q["id"])
            if ch_id and any(ch["id"] == ch_id for ch in chapters):
                q["chapterId"] = ch_id
                by_chapter.setdefault(ch_id, []).append(q)
            else:
                unclassified.append(q)

            if q["id"] in explained:
                q["explanation"] = explained[q["id"]]

        # Write per-chapter files
        for ch in chapters:
            ch_qs = by_chapter.get(ch["id"], [])
            if ch_qs:
                ch_path = subj_dir / f"{ch['id']}_quiz.json"
                ch_path.write_text(
                    json.dumps(ch_qs, ensure_ascii=False, indent=2),
                    encoding="utf-8",
                )
                print(f"    {ch['id']} ({ch['name']}): {len(ch_qs)} questions")

        if unclassified:
            unc_path = subj_dir / "unclassified_quiz.json"
            unc_path.write_text(
                json.dumps(unclassified, ensure_ascii=False, indent=2),
                encoding="utf-8",
            )
            print(f"    Unclassified: {len(unclassified)} questions")

        # Update all_quiz.json with enriched data
        quiz_file.write_text(
            json.dumps(questions, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )


def copy_to_frontend(output_dir: str) -> None:
    """Copy built quiz data to frontend public/data/realtor/."""
    src = Path(output_dir)
    dst = Path(__file__).parent.parent / "public" / "data" / "realtor"
    dst.mkdir(parents=True, exist_ok=True)

    # Copy curriculum.json
    curriculum_src = src / "curriculum.json"
    if curriculum_src.exists():
        (dst / "curriculum.json").write_text(
            curriculum_src.read_text(encoding="utf-8"),
            encoding="utf-8",
        )
        print(f"  Copied curriculum.json")

    # Copy per-subject quiz files
    for sid in SUBJECTS:
        subj_src = src / sid
        if not subj_src.exists():
            continue
        subj_dst = dst / sid
        subj_dst.mkdir(exist_ok=True)

        for json_file in subj_src.glob("*.json"):
            (subj_dst / json_file.name).write_text(
                json_file.read_text(encoding="utf-8"),
                encoding="utf-8",
            )
        print(f"  Copied {sid}/")


def main():
    parser = argparse.ArgumentParser(description="Build frontend quiz data from parsed exam questions")
    parser.add_argument("--input", "-i", default="output/parsed", help="Input directory with parsed JSON")
    parser.add_argument("--output", "-o", default="output/quiz", help="Output directory for quiz JSON")
    parser.add_argument("--with-ai", action="store_true", help="Enable Phase 2 (LLM classification)")
    parser.add_argument("--model", default="gpt-4o-mini", help="OpenAI model for Phase 2")
    parser.add_argument("--subject", "-s", help="Process single subject (e.g., s1)")
    parser.add_argument("--copy-to-frontend", action="store_true", help="Copy output to public/data/")
    args = parser.parse_args()

    print("Phase 1: Building quiz data from parsed questions...")
    build_phase1(args.input, args.output, subject_filter=args.subject)

    if args.with_ai:
        print("\nPhase 2: LLM classification and enhancement...")
        build_phase2_classify(args.input, args.output, model_name=args.model, subject_filter=args.subject)

    if args.copy_to_frontend:
        print("\nCopying to frontend...")
        copy_to_frontend(args.output)

    print("\nDone!")


if __name__ == "__main__":
    main()
