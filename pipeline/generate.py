"""
CertiPass AI Pipeline — Generate quiz JSON from exam text.

Usage:
    python generate.py input/sample_realtor_2023.txt
    python generate.py input/sample_realtor_2023.txt --output output/ch_1_quiz.json
    python generate.py input/sample_realtor_2023.txt --copy-to-frontend
"""

import argparse
import json
import shutil
import sys
from pathlib import Path

from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate

from schemas import QuizOutput

load_dotenv()

SYSTEM_PROMPT = """\
당신은 한국 국가공인자격증 시험 전문가입니다.
주어진 기출문제 텍스트를 분석하여 두 가지 유형의 학습 데이터를 생성합니다.

## 규칙

### 객관식 문제 (multiple_choice)
- 원본 기출문제를 정확히 추출합니다.
- 보기(options)는 원문 그대로 유지합니다.
- correctIndex는 0부터 시작하는 인덱스입니다 (정답이 1번이면 0, 5번이면 4).
- 해설은 원문 해설을 기반으로 간결하게 작성합니다.

### 빈칸 뚫기 (fill_in_the_blank)
- [핵심 요약] 섹션의 문장들을 기반으로 생성합니다.
- 각 문장에서 가장 중요한 핵심 키워드 하나를 [BLANK]로 치환합니다.
- answer에는 빈칸에 들어갈 정확한 단어/구를 넣습니다.
- 빈칸을 채우면 완전한 문장이 되어야 합니다.
- [BLANK]는 반드시 하나만 포함되어야 합니다.

### ID 규칙
- 객관식: q_001, q_002, ... 순서대로
- 빈칸: 객관식 이후 번호를 이어서 (예: 객관식 4개면 빈칸은 q_005부터)
"""

USER_PROMPT = """\
다음 기출문제 텍스트를 분석하여 JSON 데이터를 생성해주세요.

---
{exam_text}
---
"""


def load_input(path: str) -> str:
    """Load exam text from file."""
    text = Path(path).read_text(encoding="utf-8")
    if not text.strip():
        print(f"Error: Input file is empty: {path}", file=sys.stderr)
        sys.exit(1)
    return text


def generate_quiz(exam_text: str, model_name: str = "gpt-4o-mini") -> QuizOutput:
    """Run LangChain structured output pipeline."""
    llm = ChatOpenAI(model=model_name, temperature=0)
    structured_llm = llm.with_structured_output(QuizOutput)

    prompt = ChatPromptTemplate.from_messages([
        ("system", SYSTEM_PROMPT),
        ("human", USER_PROMPT),
    ])

    chain = prompt | structured_llm
    result = chain.invoke({"exam_text": exam_text})
    return result


def to_json_list(quiz: QuizOutput) -> list[dict]:
    """Convert QuizOutput to the flat JSON array format expected by frontend."""
    items = []
    for mc in quiz.multiple_choice:
        items.append(mc.model_dump())
    for fb in quiz.fill_in_the_blank:
        items.append(fb.model_dump())
    return items


def main():
    parser = argparse.ArgumentParser(description="Generate quiz JSON from exam text")
    parser.add_argument("input", help="Path to input exam text file")
    parser.add_argument("--output", "-o", help="Output JSON file path")
    parser.add_argument(
        "--copy-to-frontend",
        action="store_true",
        help="Also copy output to public/data/ for frontend use",
    )
    parser.add_argument(
        "--model",
        default="gpt-4o-mini",
        help="OpenAI model to use (default: gpt-4o-mini)",
    )
    args = parser.parse_args()

    # Load input
    print(f"📖 Loading: {args.input}")
    exam_text = load_input(args.input)

    # Parse metadata from text
    lines = exam_text.strip().split("\n")
    meta = {}
    for line in lines[:10]:
        if ":" in line:
            key, val = line.split(":", 1)
            meta[key.strip()] = val.strip()

    print(f"📋 자격증: {meta.get('자격증', '?')}")
    print(f"📋 과목: {meta.get('과목', '?')}")
    print(f"📋 단원: {meta.get('단원', '?')}")
    print(f"🤖 Model: {args.model}")
    print("⏳ Generating quiz data...")

    # Generate
    quiz = generate_quiz(exam_text, model_name=args.model)

    print(f"✅ Generated: {len(quiz.multiple_choice)} multiple choice, "
          f"{len(quiz.fill_in_the_blank)} fill-in-the-blank")

    # Convert to frontend format
    json_data = to_json_list(quiz)

    # Determine output path
    output_path = args.output
    if not output_path:
        Path("output").mkdir(exist_ok=True)
        output_path = "output/quiz_output.json"

    # Write output
    Path(output_path).write_text(
        json.dumps(json_data, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    print(f"💾 Saved: {output_path}")

    # Optionally copy to frontend
    if args.copy_to_frontend:
        frontend_path = Path(__file__).parent.parent / "public" / "data"
        if frontend_path.exists():
            dest = frontend_path / "realtor" / "sub_1" / "ch_1_quiz.json"
            dest.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(output_path, dest)
            print(f"📦 Copied to frontend: {dest}")
        else:
            print("⚠️  Frontend public/data/ not found, skipping copy")

    # Preview
    print("\n--- Preview (first 2 items) ---")
    for item in json_data[:2]:
        print(json.dumps(item, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
