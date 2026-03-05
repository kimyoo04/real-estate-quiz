# CertiPass - 공인중개사 기출문제 학습 앱

[![Deploy](https://github.com/kimyoo04/certi-pass/actions/workflows/deploy.yml/badge.svg)](https://github.com/kimyoo04/certi-pass/actions/workflows/deploy.yml)

공인중개사 시험 대비를 위한 모바일 최적화 웹 학습 앱입니다. 연도별 기출문제 풀이, OX 퀴즈, 빈칸 뚫기, 모의고사, 플래시카드, 개념 트리 등 다양한 학습 기능을 제공합니다.

> **Live**: [https://kimyoo04.github.io/certi-pass/](https://kimyoo04.github.io/certi-pass/)

## 주요 기능

### 학습
- **기출문제 풀기** — 과목별/연도별 객관식 문제 풀이 (2016~2024년), 즉시 해설 확인
- **OX 퀴즈** — 핵심 개념을 O/X로 빠르게 확인 (과목당 50~78개, 총 384개)
- **빈칸 뚫기** — 핵심 키워드를 가리고 떠올리며 암기 (과목당 21~75개, 총 282개)
- **오답 복습** — 틀린 문제만 모아서 재학습
- **북마크** — 중요 문제를 북마크하여 별도로 관리
- **문제 셔플** — Fisher-Yates 알고리즘 기반 무작위 출제
- **SM-2 정렬** — 간격 반복 알고리즘(SM-2) 기반으로 복습이 필요한 문제를 우선 출제

### 시험
- **모의고사** — 실전과 동일한 타이머 기반 모의시험 (과목별 문제 수/시간 설정)
- **대시보드** — D-day 카운트다운, 학습 히트맵, 과목별 정답률, 취약 영역 분석, 모의고사 이력
- **문제 검색** — 키워드 하이라이팅, 타입 필터(객관식/빈칸), 최근 검색 기록

### 개념 정리
- **개념 트리** — 과목별 계층 구조로 정리된 출제 범위 (대단원 > 중단원 > 소단원)
- **문제 분류** — 기출문제를 개념 트리 노드에 매핑
- **플래시카드** — 과목별 핵심 용어/개념을 카드 뒤집기 방식으로 암기
  - 3D 뒤집기 애니메이션 (앞면: 키워드, 뒷면: 정의)
  - 좌우 스와이프 / 키보드 방향키 네비게이션
  - 카드 직접 추가·수정·삭제 (localStorage 저장)
  - 카테고리 셀렉트 + 새 카테고리 추가

### 모바일 UX
- **Safe Area 지원** — 노치/홈 인디케이터 영역 자동 대응
- **Sticky 하단 내비게이션** — 퀴즈, 빈칸 뚫기, 모의고사 페이지에서 버튼 고정
- **스와이프 내비게이션** — 좌우 스와이프로 문제 전환
- **다크 모드** — 시스템 설정 연동 + 수동 전환

### 접근성 (a11y)
- ARIA 속성: `role="timer"`, `aria-live`, `aria-expanded`, `aria-current` 등
- 키보드 내비게이션: 카드 요소에 `tabIndex`, `onKeyDown` 지원
- 시맨틱 HTML: 로딩 스피너 `role="status"`, 알림 `role="alert"`

### Dev Mode (개발 전용)
- **문제 편집** — 퀴즈/빈칸 페이지에서 연필 아이콘으로 문제 내용 직접 수정
- **Production 안전** — 모든 dev 코드는 빌드 시 tree-shaken되어 프로덕션에 포함되지 않음

## 기술 스택

| 영역 | 기술 |
|------|------|
| Framework | React 19, TypeScript 5.9 |
| Build | Vite 7 |
| Routing | React Router DOM 7 (HashRouter) |
| State | Zustand 5 (+ persist middleware → localStorage) |
| Styling | Tailwind CSS 4 |
| UI Components | Radix UI + shadcn/ui |
| Icons | Lucide React |
| Testing | Vitest + Testing Library + @vitest/coverage-v8 |
| Deploy | GitHub Pages (GitHub Actions CI/CD) |
| Email | EmailJS |

## 프로젝트 구조

```
src/
├── components/          # 공통 컴포넌트
│   ├── ui/              # shadcn/ui 기반 UI 컴포넌트
│   ├── activity-heatmap.tsx  # 학습 히트맵
│   ├── mobile-layout.tsx
│   ├── question-edit-dialog.tsx  # [Dev] 문제 편집 다이얼로그
│   └── tree-node-*.tsx  # 트리 관련 컴포넌트
├── pages/               # 라우트별 페이지
│   ├── subject-page.tsx       # 과목 선택 (홈)
│   ├── quiz-page.tsx          # 기출문제 풀기
│   ├── fill-blank-page.tsx    # 빈칸 뚫기
│   ├── ox-quiz-page.tsx       # OX 퀴즈
│   ├── mock-exam-page.tsx     # 모의고사
│   ├── dashboard-page.tsx     # 학습 현황
│   ├── search-page.tsx        # 문제 검색
│   ├── flashcard-page.tsx     # 플래시카드
│   └── tree-view-page.tsx     # 개념 트리
├── stores/              # Zustand 상태 관리
│   ├── use-quiz-store.ts      # 퀴즈 진행 + 학습 활동 로그
│   ├── use-sm2-store.ts       # SM-2 간격 반복 데이터
│   ├── use-settings-store.ts  # D-day 등 앱 설정
│   ├── use-mock-exam-store.ts
│   ├── use-flashcard-store.ts
│   └── use-bookmark-store.ts
├── utils/               # 유틸리티
│   ├── sm2.ts           # SM-2 알고리즘
│   ├── shuffle.ts
│   └── stats-utils.ts
├── types/               # TypeScript 타입 정의
├── hooks/               # 커스텀 훅 (useCachedFetch, useSwipe 등)
└── __tests__/           # 테스트

public/data/
└── realtor/             # 공인중개사 데이터
    ├── curriculum.json  # 과목/챕터 목록
    └── s{1-6}/          # 과목별 폴더
        ├── all_quiz.json          # 객관식 + 빈칸 뚫기 문제
        ├── ox_quiz.json           # OX 퀴즈 문제
        ├── y{year}_quiz.json      # 연도별 기출문제
        ├── question_tree_map.json
        └── flashcards.json
```

## 시작하기

```bash
# 의존성 설치
pnpm install

# 개발 서버 시작
pnpm dev

# 프로덕션 빌드
pnpm build

# 테스트 실행
pnpm vitest run

# 테스트 커버리지 확인
pnpm vitest run --coverage

# 린트
pnpm lint
```

## 문제 데이터 생성 스크립트

Ollama(llama3.1)를 이용해 로컬에서 AI 문제를 생성할 수 있습니다.

```bash
# Ollama 실행 (별도 터미널)
ollama serve

# 빈칸 뚫기 문제 생성 (과목당 ~60개)
python3 scripts/generate_blanks.py

# OX 퀴즈 문제 생성 (과목당 ~60개)
python3 scripts/generate_ox.py

# OX 퀴즈 샘플 데이터 시드 (Ollama 없이 실행 가능)
python3 scripts/seed_ox_quiz.py
```

## 테스트 현황

| 영역 | Statements | Functions | Lines |
|------|-----------|-----------|-------|
| stores | 96% | 100% | 97% |
| utils | 85% | 80% | 87% |
| pages | ~74% | ~64% | ~75% |
| **전체** | **74%** | **64%** | **75%** |

- **28개** 테스트 파일 / **315개** 테스트 케이스
- TypeScript, ESLint 에러 0건

## 과목 목록 및 문제 현황

| ID | 과목명 | 기출문제(객관식) | 빈칸 뚫기 | OX 퀴즈 |
|----|--------|:--------------:|:---------:|:-------:|
| s1 | 부동산학개론 | 280문제 | 40개 | 52개 |
| s2 | 민법 및 민사특별법 | 277문제 | 75개 | 65개 |
| s3 | 부동산공법 | 233문제 | 24개 | 73개 |
| s4 | 부동산공시법령 | 121문제 | 54개 | 52개 |
| s5 | 공인중개사법령 및 중개실무 | 280문제 | 21개 | 78개 |
| s6 | 부동산세법 | 118문제 | 68개 | 64개 |
| **합계** | | **1,309문제** | **282개** | **384개** |

## 플래시카드 데이터 추가 방법

웹에서 카드를 추가하면 localStorage에 임시 저장됩니다. 영구 반영하려면:

1. 과목 선택 → **개념 플래시카드** → 과목 선택 → **편집** 버튼
2. 카드 추가·수정 후 **JSON 내보내기** 클릭
3. 다운로드된 파일을 `public/data/realtor/s{N}/flashcards.json`으로 교체
4. 커밋 후 push → GitHub Actions가 자동 배포

`flashcards.json` 구조:

```json
{
  "subjectId": "s1",
  "subjectName": "부동산학개론",
  "cards": [
    {
      "id": "s1_fc001",
      "term": "부동성",
      "definition": "토지는 위치가 고정되어 이동이 불가능한 특성.",
      "category": "토지의 특성"
    }
  ]
}
```
