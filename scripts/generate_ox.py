#!/usr/bin/env python3
"""
공인중개사 시험 OX 퀴즈 문제 생성기 (Ollama llama3.1 사용)

사용법:
  1. ollama 실행: ollama serve
  2. 모델 준비:  ollama pull llama3.1
  3. 스크립트:   python3 scripts/generate_ox.py

결과: public/data/realtor/{subjectId}/ox_quiz.json 에 OX 문제 저장
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
    text = re.sub(r"```(?:json)?", "", text).strip().rstrip("`").strip()
    start = text.find("[")
    end   = text.rfind("]")
    if start == -1 or end == -1:
        raise ValueError("JSON 배열을 찾을 수 없음")
    return json.loads(text[start : end + 1])


def validate_question(q: dict) -> bool:
    return (
        isinstance(q.get("statement"), str) and q["statement"].strip()
        and isinstance(q.get("answer"), bool)
        and isinstance(q.get("explanation"), str) and q["explanation"].strip()
    )


# ─── 프롬프트 ─────────────────────────────────────────────────────────────────

def build_prompt(subject_name: str, sample_questions: list, existing_statements: set) -> str:
    samples_text = "\n".join(
        f"- {q['content']}" for q in sample_questions[:20]
    )
    existing_hint = (
        ("이미 생성된 지문(중복 금지 키워드): " + " / ".join(list(existing_statements)[:20]))
        if existing_statements else ""
    )

    return f"""당신은 한국 공인중개사 시험 전문 교육 콘텐츠 제작자입니다.

과목: {subject_name}

아래는 이 과목의 실제 기출문제 일부입니다 (맥락 참고용):
{samples_text}

{existing_hint}

위 과목의 핵심 개념·법조문·수치를 다루는 OX 퀴즈 {BATCH_SIZE}개를 만들어주세요.

규칙:
1. 각 문제는 하나의 서술문(statement)으로 구성됩니다
2. answer는 true(O) 또는 false(X)입니다 — 반드시 참/거짓이 명확해야 합니다
3. O 문제와 X 문제를 고르게 섞어주세요 (50:50 비율)
4. X 문제는 틀린 부분이 명확해야 합니다 (숫자, 조건, 용어 등)
5. explanation은 왜 O인지 또는 왜 X인지 1-2문장으로 간결하게 설명하세요
6. 중요한 법률 개념, 기간, 비율, 금액, 요건 등을 다루는 문제를 만드세요
7. 이미 생성된 지문과 겹치지 않도록 하세요

반드시 아래 JSON 배열 형식으로만 응답하세요 (다른 텍스트 없이):
[
  {{
    "statement": "서술문",
    "answer": true,
    "explanation": "해설"
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

    print(f"\n{'='*60}")
    print(f"📚 {subject_name} ({subject_id})")
    print(f"   기출문제: {len(mc_questions)}개")

    new_questions = []
    existing_statements: set = set()
    batches = (TARGET_COUNT + BATCH_SIZE - 1) // BATCH_SIZE

    for batch in range(batches):
        print(f"  📝 배치 {batch+1}/{batches} 생성 중... (현재 {len(new_questions)}개)", flush=True)

        import random
        sample = random.sample(mc_questions, min(20, len(mc_questions)))
        prompt = build_prompt(subject_name, sample, existing_statements)

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
                    existing_statements.add(q["statement"][:30])
                new_questions.extend(valid)
                print(f"    ✅ {len(valid)}개 생성 (누적 {len(new_questions)}개)")
                break
            except Exception as e:
                print(f"    ❌ 오류: {e} (재시도 {attempt+1})")
                time.sleep(3)

        time.sleep(1)

    return new_questions


def assign_ids(questions: list, subject_id: str) -> list:
    result = []
    for i, q in enumerate(questions, start=1):
        result.append({
            "id": f"{subject_id}_ox_{i:04d}",
            "type": "ox_quiz",
            "statement": q["statement"].strip(),
            "answer": bool(q["answer"]),
            "explanation": q.get("explanation", "").strip(),
        })
    return result


def save_ox_quiz(subject_id: str, questions: list) -> int:
    out_path = DATA_DIR / subject_id / "ox_quiz.json"
    out_path.write_text(
        json.dumps(questions, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    return len(questions)


# ─── 진입점 ──────────────────────────────────────────────────────────────────

def main():
    print("🚀 OX 퀴즈 문제 생성기 (Ollama llama3.1)")
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

        new_qs = generate_for_subject(subject_id, subject_name)

        if not new_qs:
            print(f"  ⚠️  생성된 문제 없음")
            results[subject_name] = 0
            continue

        with_ids = assign_ids(new_qs, subject_id)
        saved = save_ox_quiz(subject_id, with_ids)
        total_generated += len(with_ids)
        results[subject_name] = saved

        print(f"  💾 저장 완료: {saved}개")

    print(f"\n{'='*60}")
    print("📊 최종 결과")
    for name, count in results.items():
        print(f"   {name}: {count}개")
    print(f"\n🎉 총 신규 생성: {total_generated}개")


if __name__ == "__main__":
    main()
