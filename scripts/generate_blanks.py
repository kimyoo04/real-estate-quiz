#!/usr/bin/env python3
"""
공인중개사 시험 빈칸 뚫기 문제 생성기 (Ollama llama3.1 사용)

사용법:
  1. ollama 실행: ollama serve
  2. 모델 준비:  ollama pull llama3.1
  3. 스크립트:   python3 scripts/generate_blanks.py

결과: public/data/realtor/{subjectId}/all_quiz.json 에 fill_in_the_blank 문제 추가
"""

import json
import re
import sys
import time
from pathlib import Path

import urllib.request
import urllib.error

# ─── 설정 ────────────────────────────────────────────────────────────────────

OLLAMA_URL   = "http://localhost:11434/api/chat"
MODEL        = "llama3.1"
DATA_DIR     = Path(__file__).parent.parent / "public" / "data" / "realtor"
TARGET_COUNT = 60   # 과목당 생성 목표 (배치당 20개 × 3배치)
BATCH_SIZE   = 20   # 한 번에 요청할 문제 수
TEMPERATURE  = 0.4

SUBJECTS = {
    "s1": "부동산학개론",
    "s2": "민법 및 민사특별법",
    "s3": "부동산공법",
    "s4": "부동산공시법령",
    "s5": "공인중개사법령 및 중개실무",
    "s6": "부동산세법",
}

# ─── Ollama 호출 ──────────────────────────────────────────────────────────────

def check_ollama() -> bool:
    try:
        req = urllib.request.urlopen("http://localhost:11434/api/tags", timeout=3)
        return req.status == 200
    except Exception:
        return False


def call_ollama(prompt: str) -> str:
    payload = json.dumps({
        "model": MODEL,
        "messages": [{"role": "user", "content": prompt}],
        "stream": False,
        "options": {"temperature": TEMPERATURE},
    }).encode()

    req = urllib.request.Request(
        OLLAMA_URL,
        data=payload,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=120) as resp:
        result = json.loads(resp.read())
    return result["message"]["content"]


# ─── JSON 파싱 ───────────────────────────────────────────────────────────────

def extract_json_array(text: str) -> list:
    """LLM 응답에서 JSON 배열만 추출한다."""
    # ```json ... ``` 블록 제거
    text = re.sub(r"```(?:json)?", "", text).strip().rstrip("`").strip()
    # 첫 번째 '[' 부터 마지막 ']' 까지 추출
    start = text.find("[")
    end   = text.rfind("]")
    if start == -1 or end == -1:
        raise ValueError("JSON 배열을 찾을 수 없음")
    return json.loads(text[start : end + 1])


def validate_question(q: dict) -> bool:
    return (
        isinstance(q.get("content"), str) and "___" in q["content"]
        and isinstance(q.get("answer"), str) and q["answer"].strip()
        and isinstance(q.get("explanation"), str)
    )


# ─── 프롬프트 ─────────────────────────────────────────────────────────────────

def build_prompt(subject_name: str, sample_questions: list, batch_n: int, existing_answers: set) -> str:
    samples_text = "\n".join(
        f"- {q['content']}" for q in sample_questions[:25]
    )
    existing_hint = (
        ("이미 생성된 정답 단어(중복 금지): " + ", ".join(list(existing_answers)[:30]))
        if existing_answers else ""
    )

    return f"""당신은 한국 공인중개사 시험 전문 교육 콘텐츠 제작자입니다.

과목: {subject_name}

아래는 이 과목의 실제 기출문제 일부입니다 (맥락 참고용):
{samples_text}

{existing_hint}

위 과목의 핵심 개념·법조문·수치를 다루는 빈칸 뚫기 문제 {BATCH_SIZE}개를 만들어주세요.

규칙:
1. 반드시 중요한 법률 용어, 기간(일수·연수), 비율(%), 조건, 금액 등을 빈칸으로 만들어야 합니다
2. 빈칸은 반드시 "( ___ )" 형식으로 표기하세요 (공백 포함)
3. 각 문제에는 빈칸이 정확히 1개만 있어야 합니다
4. 정답(answer)은 빈칸에 들어갈 단어/구문입니다
5. 해설(explanation)은 1-2문장으로 간결하게 작성하세요
6. 쉬운 문제부터 어려운 문제까지 다양하게 만드세요
7. 이미 생성된 정답 단어와 중복되지 않도록 하세요

반드시 아래 JSON 배열 형식으로만 응답하세요 (다른 텍스트 없이):
[
  {{
    "content": "문장 ( ___ ) 나머지 문장",
    "answer": "정답 단어",
    "explanation": "이 개념에 대한 간결한 해설"
  }}
]"""


# ─── 메인 로직 ───────────────────────────────────────────────────────────────

def generate_for_subject(subject_id: str, subject_name: str) -> list:
    quiz_path = DATA_DIR / subject_id / "all_quiz.json"
    if not quiz_path.exists():
        print(f"  ⚠️  {quiz_path} 없음, 건너뜀")
        return []

    all_data: list = json.loads(quiz_path.read_text(encoding="utf-8"))
    mc_questions = [q for q in all_data if q.get("type") == "multiple_choice"]
    existing_blanks = [q for q in all_data if q.get("type") == "fill_in_the_blank"]

    print(f"\n{'='*60}")
    print(f"📚 {subject_name} ({subject_id})")
    print(f"   기출문제: {len(mc_questions)}개 | 기존 빈칸: {len(existing_blanks)}개")

    new_questions = []
    existing_answers: set = {q.get("answer", "") for q in existing_blanks}
    batches = (TARGET_COUNT + BATCH_SIZE - 1) // BATCH_SIZE

    for batch in range(batches):
        already = len(existing_blanks) + len(new_questions)
        print(f"  📝 배치 {batch+1}/{batches} 생성 중... (현재 {already}개)", flush=True)

        # 매 배치마다 다른 샘플 사용
        import random
        sample = random.sample(mc_questions, min(25, len(mc_questions)))
        prompt = build_prompt(subject_name, sample, batch, existing_answers)

        for attempt in range(3):
            try:
                raw = call_ollama(prompt)
                items = extract_json_array(raw)
                valid = [q for q in items if validate_question(q)]
                if not valid:
                    print(f"    ⚠️  유효한 문제 없음 (재시도 {attempt+1})")
                    time.sleep(2)
                    continue

                for q in valid:
                    existing_answers.add(q["answer"])
                new_questions.extend(valid)
                print(f"    ✅ {len(valid)}개 생성 (누적 {len(new_questions)}개)")
                break
            except Exception as e:
                print(f"    ❌ 오류: {e} (재시도 {attempt+1})")
                time.sleep(3)

        time.sleep(1)  # 배치 간 짧은 대기

    return new_questions


def assign_ids(questions: list, subject_id: str, start_n: int) -> list:
    result = []
    for i, q in enumerate(questions, start=start_n):
        result.append({
            "id": f"{subject_id}_blank_{i:04d}",
            "type": "fill_in_the_blank",
            "content": q["content"].strip(),
            "answer": q["answer"].strip(),
            "explanation": q.get("explanation", "").strip(),
        })
    return result


def save_to_all_quiz(subject_id: str, new_blanks: list) -> int:
    quiz_path = DATA_DIR / subject_id / "all_quiz.json"
    all_data: list = json.loads(quiz_path.read_text(encoding="utf-8"))

    # 기존 blank 제거 후 새것으로 교체
    mc_only = [q for q in all_data if q.get("type") == "multiple_choice"]
    merged = mc_only + new_blanks

    quiz_path.write_text(
        json.dumps(merged, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    return len(new_blanks)


# ─── 진입점 ──────────────────────────────────────────────────────────────────

def main():
    print("🚀 빈칸 뚫기 문제 생성기 (Ollama llama3.1)")
    print(f"   모델: {MODEL} | 과목당 목표: {TARGET_COUNT}개\n")

    if not check_ollama():
        print("❌ Ollama가 실행되지 않았습니다.")
        print("   다음 명령어로 실행하세요:")
        print("     ollama serve")
        print("     ollama pull llama3.1")
        sys.exit(1)

    print("✅ Ollama 연결 확인")

    total_generated = 0
    results: dict[str, int] = {}

    for subject_id, subject_name in SUBJECTS.items():
        quiz_path = DATA_DIR / subject_id / "all_quiz.json"
        if not quiz_path.exists():
            continue

        # 기존 blank 수 파악
        existing = json.loads(quiz_path.read_text(encoding="utf-8"))
        existing_blanks = [q for q in existing if q.get("type") == "fill_in_the_blank"]
        start_n = len(existing_blanks) + 1

        new_qs = generate_for_subject(subject_id, subject_name)

        if not new_qs:
            print(f"  ⚠️  생성된 문제 없음")
            results[subject_name] = 0
            continue

        with_ids = assign_ids(new_qs, subject_id, start_n)
        # 기존 blank + 새 blank 합산
        all_existing_blanks = [q for q in existing if q.get("type") == "fill_in_the_blank"]
        final_blanks = all_existing_blanks + with_ids

        saved = save_to_all_quiz(subject_id, final_blanks)
        total_generated += len(with_ids)
        results[subject_name] = saved

        print(f"  💾 저장 완료: {saved}개 (신규 {len(with_ids)}개)")

    print(f"\n{'='*60}")
    print("📊 최종 결과")
    for name, count in results.items():
        print(f"   {name}: {count}개")
    print(f"\n🎉 총 신규 생성: {total_generated}개")


if __name__ == "__main__":
    main()
