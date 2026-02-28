# CertiPass AI Pipeline

기출문제 텍스트를 프론트엔드 JSON 데이터로 변환하는 AI 파이프라인.

## Setup

```bash
cd pipeline
python3 -m venv .venv
source .venv/bin/activate
pip install langchain langchain-openai pydantic python-dotenv
```

## Configuration

```bash
cp .env.example .env
# .env 파일에 OpenAI API 키 입력
```

## Usage

```bash
# 기본 실행 (output/quiz_output.json 생성)
python generate.py input/sample_realtor_2023.txt

# 출력 경로 지정
python generate.py input/sample_realtor_2023.txt -o output/ch_1_quiz.json

# 프론트엔드에 바로 복사
python generate.py input/sample_realtor_2023.txt --copy-to-frontend

# GPT-4o 사용 (더 정확)
python generate.py input/sample_realtor_2023.txt --model gpt-4o
```

## Input Format

텍스트 파일에 다음 형식으로 작성:

```
자격증: 공인중개사
과목: 부동산학개론
단원: 부동산의 개념과 특성
연도: 2023

[문제 1]
문제 내용...
① 보기1
② 보기2
...
정답: 1
해설: 해설 내용

[핵심 요약]
- 빈칸 뚫기로 변환될 핵심 문장들
```

## Output

프론트엔드 `public/data/` 구조에 맞는 JSON 배열 생성:

```json
[
  { "id": "q_001", "type": "multiple_choice", ... },
  { "id": "q_005", "type": "fill_in_the_blank", ... }
]
```
