"""
GPT를 사용하여 정답이 없는 기출문제의 정답을 판별합니다.

Usage:
    python fill_answers.py                          # 정답 없는 문제 판별
    python fill_answers.py --dry-run                # 실행 없이 대상 문제 수만 확인
    python fill_answers.py --subject s1             # 특정 과목만 처리
"""

import argparse
import json
import time
from pathlib import Path

from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

BATCH_SIZE = 15  # questions per API call
MODEL = "gpt-4o-mini"

SYSTEM_PROMPT = """\
당신은 한국 공인중개사 자격시험 전문가입니다.
주어진 기출문제의 정답 번호(1~5)를 판별해주세요.

규칙:
- 각 문제의 정답을 1~5 중 하나로 선택합니다.
- JSON 배열로 응답합니다: [{"id": "문제ID", "answer": 정답번호}]
- 정답번호는 1부터 5까지의 정수입니다.
- 확실하지 않은 경우에도 가장 가능성 높은 답을 선택합니다.
- JSON만 응답하고 다른 텍스트는 포함하지 마세요.
"""


def load_questions(input_path: str) -> list[dict]:
    """Load all parsed questions."""
    path = Path(input_path) / "all_questions.json"
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def filter_candidates(questions: list[dict], subject: str | None = None) -> list[dict]:
    """Filter questions that need answers and have 5 valid options."""
    candidates = []
    for q in questions:
        # Skip if already has answer
        if q.get("answer"):
            continue
        # Must have known subject
        sid = q.get("subject_id")
        if not sid or sid == "unknown":
            continue
        # Filter by subject if specified
        if subject and sid != subject:
            continue
        # Must have exactly 5 options
        opts = q.get("options", [])
        if len(opts) != 5:
            continue
        # Options must have reasonable content
        if any(len(o.strip()) < 2 for o in opts):
            continue
        # Content must be meaningful
        if len(q.get("content", "").strip()) < 10:
            continue
        candidates.append(q)
    return candidates


def format_question(q: dict, idx: int) -> str:
    """Format a question for the GPT prompt."""
    lines = [
        f"[문제 {idx}] ID: {q.get('subject_id')}_{q.get('year', '?')}_Q{q['number']}"
    ]
    lines.append(q["content"])
    for i, opt in enumerate(q["options"], 1):
        lines.append(f"  {i}. {opt}")
    return "\n".join(lines)


def call_gpt(client: OpenAI, batch: list[dict]) -> list[dict]:
    """Call GPT to determine answers for a batch of questions."""
    questions_text = "\n\n".join(format_question(q, i + 1) for i, q in enumerate(batch))

    response = client.chat.completions.create(
        model=MODEL,
        temperature=0,
        response_format={"type": "json_object"},
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {
                "role": "user",
                "content": f'다음 {len(batch)}개 문제의 정답을 판별해주세요:\n\n{questions_text}\n\nJSON 형식: {{"answers": [{{"id": "...", "answer": N}}]}}',
            },
        ],
    )

    try:
        result = json.loads(response.choices[0].message.content)
        return result.get("answers", [])
    except (json.JSONDecodeError, AttributeError):
        return []


def main():
    parser = argparse.ArgumentParser(description="Fill missing answers using GPT")
    parser.add_argument(
        "--input", "-i", default="output/parsed", help="Input directory"
    )
    parser.add_argument("--subject", "-s", help="Process single subject")
    parser.add_argument(
        "--dry-run", action="store_true", help="Show stats without calling API"
    )
    args = parser.parse_args()

    questions = load_questions(args.input)
    candidates = filter_candidates(questions, subject=args.subject)

    print(f"Total questions: {len(questions)}")
    print(f"Already have answers: {sum(1 for q in questions if q.get('answer'))}")
    print(f"Candidates for GPT answer fill: {len(candidates)}")

    # Show breakdown
    from collections import Counter

    by_subj = Counter(q.get("subject_id") for q in candidates)
    for sid, count in sorted(by_subj.items()):
        years = sorted(
            set(q.get("year") or 0 for q in candidates if q.get("subject_id") == sid)
        )
        print(f"  {sid}: {count} questions, years: {min(years)}-{max(years)}")

    if args.dry_run:
        est_calls = (len(candidates) + BATCH_SIZE - 1) // BATCH_SIZE
        print(f"\nEstimated API calls: {est_calls}")
        print(f"Estimated cost: ~${est_calls * 0.001:.3f} (gpt-4o-mini)")
        return

    if not candidates:
        print("No candidates to process.")
        return

    # Build lookup: (subject_id, year, number) → question index
    q_lookup: dict[tuple, int] = {}
    for i, q in enumerate(questions):
        key = (q.get("subject_id"), q.get("year"), q.get("number"))
        q_lookup[key] = i

    client = OpenAI()
    filled = 0
    errors = 0

    for batch_start in range(0, len(candidates), BATCH_SIZE):
        batch = candidates[batch_start : batch_start + BATCH_SIZE]
        batch_end = min(batch_start + BATCH_SIZE, len(candidates))

        try:
            results = call_gpt(client, batch)

            for item in results:
                ans = item.get("answer")
                if not isinstance(ans, int) or ans < 1 or ans > 5:
                    continue

                # Parse ID back to find the question
                qid = item.get("id", "")
                # ID format: {subject_id}_{year}_Q{number}
                parts = qid.split("_")
                if len(parts) >= 3:
                    try:
                        sid = parts[0]
                        year = int(parts[1]) if parts[1] != "?" else None
                        num = int(parts[2].replace("Q", ""))
                        key = (sid, year, num)
                        if key in q_lookup:
                            questions[q_lookup[key]]["answer"] = ans
                            questions[q_lookup[key]]["answer_source"] = "gpt"
                            filled += 1
                    except (ValueError, IndexError):
                        pass

            print(
                f"  Batch {batch_start + 1}-{batch_end}/{len(candidates)}: {len(results)} answers",
                end="\r",
            )

        except Exception as e:
            print(f"\n  Error at batch {batch_start}: {e}")
            errors += 1
            time.sleep(2)

        # Rate limiting
        time.sleep(0.3)

    print(f"\nFilled {filled} answers ({errors} errors)")

    # Save updated questions
    output_path = Path(args.input) / "all_questions.json"
    output_path.write_text(
        json.dumps(questions, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    print(f"Saved: {output_path}")

    # Summary
    total_with = sum(1 for q in questions if q.get("answer"))
    gpt_filled = sum(1 for q in questions if q.get("answer_source") == "gpt")
    print(
        f"\nTotal with answers now: {total_with} (original: {total_with - gpt_filled}, GPT: {gpt_filled})"
    )


if __name__ == "__main__":
    main()
