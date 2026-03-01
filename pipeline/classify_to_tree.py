"""
Classify exam questions to tree nodes using LLM.

Reads questions from quiz JSON files and the tree structure from examTree.ts,
then uses GPT to map each question to the most appropriate tree node.

Usage:
    python classify_to_tree.py [--subject s1] [--dry-run]
"""

import argparse
import json
import os
import re
import sys
from pathlib import Path

from openai import OpenAI

# ── Paths ──
PROJECT_ROOT = Path(__file__).resolve().parent.parent
FRONTEND_DATA = PROJECT_ROOT / "public" / "data" / "realtor"
TREE_JSON = Path(__file__).resolve().parent / "data" / "exam_tree.json"

SUBJECTS = ["s1", "s2", "s3", "s4", "s5", "s6"]

BATCH_SIZE = 10  # questions per GPT call


def load_tree(subject_id: str) -> list[dict]:
    """Load tree nodes for a subject from exam_tree.json."""
    if not TREE_JSON.exists():
        print(f"Error: {TREE_JSON} not found. Run extract_tree first.")
        sys.exit(1)
    data = json.loads(TREE_JSON.read_text(encoding="utf-8"))
    return data.get(subject_id, [])


def flatten_tree_nodes(nodes: list[dict], prefix: str = "") -> list[dict]:
    """Flatten tree to a list of {id, label, path} dicts."""
    result = []
    for node in nodes:
        path = f"{prefix}{node['label']}" if not prefix else f"{prefix} > {node['label']}"
        result.append({"id": node["id"], "label": node["label"], "path": path})
        if node.get("children"):
            result.extend(flatten_tree_nodes(node["children"], path))
    return result


def load_questions(subject_id: str) -> list[dict]:
    """Load all quiz questions for a subject."""
    subj_dir = FRONTEND_DATA / subject_id
    all_quiz = subj_dir / "all_quiz.json"
    if all_quiz.exists():
        return json.loads(all_quiz.read_text(encoding="utf-8"))
    # Fallback: merge year files
    questions = []
    for f in sorted(subj_dir.glob("y*_quiz.json")):
        questions.extend(json.loads(f.read_text(encoding="utf-8")))
    return questions


def classify_batch(
    client: OpenAI,
    questions: list[dict],
    tree_nodes: list[dict],
    model: str = "gpt-4o-mini",
) -> dict[str, str | None]:
    """Classify a batch of questions to tree nodes using GPT."""
    node_list = "\n".join(
        f"  {n['id']}: {n['path']}" for n in tree_nodes
    )

    q_list = "\n---\n".join(
        f"ID: {q['id']}\n문제: {q['content']}\n"
        + (
            "보기: "
            + " / ".join(
                f"{i+1}) {opt['text']}" for i, opt in enumerate(q.get("options", []))
            )
            if q.get("options")
            else ""
        )
        for q in questions
    )

    prompt = f"""다음은 공인중개사 시험 문제들입니다. 각 문제를 아래 개념 트리 노드 중 가장 적합한 노드에 분류해주세요.

## 개념 트리 노드 목록
{node_list}

## 문제들
{q_list}

## 출력 형식
각 문제 ID에 대해 가장 적합한 노드 ID를 JSON 객체로 반환하세요.
분류할 수 없는 문제는 null로 표시하세요.

예시:
{{"s1_q0001": "s1-m1-c2-t1", "s1_q0002": null}}

JSON만 출력하세요."""

    resp = client.chat.completions.create(
        model=model,
        messages=[{"role": "user", "content": prompt}],
        temperature=0,
        response_format={"type": "json_object"},
    )

    text = resp.choices[0].message.content or "{}"
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        # Try to extract JSON from the response
        match = re.search(r"\{[^{}]*\}", text, re.DOTALL)
        if match:
            return json.loads(match.group())
        return {}


def classify_subject(
    subject_id: str,
    dry_run: bool = False,
    model: str = "gpt-4o-mini",
) -> dict:
    """Classify all questions for a subject."""
    tree_nodes_raw = load_tree(subject_id)
    if not tree_nodes_raw:
        print(f"  No tree nodes for {subject_id}, skipping")
        return {"classified": {}, "unclassified": []}

    flat_nodes = flatten_tree_nodes(tree_nodes_raw)
    questions = load_questions(subject_id)

    if not questions:
        print(f"  No questions for {subject_id}")
        return {"classified": {}, "unclassified": []}

    print(f"  {len(questions)} questions, {len(flat_nodes)} tree nodes")

    if dry_run:
        return {"classified": {}, "unclassified": [{"id": q["id"]} for q in questions]}

    client = OpenAI()
    classified: dict[str, str] = {}
    unclassified: list[dict] = []
    valid_ids = {n["id"] for n in flat_nodes}

    for i in range(0, len(questions), BATCH_SIZE):
        batch = questions[i : i + BATCH_SIZE]
        print(f"    Batch {i // BATCH_SIZE + 1}/{(len(questions) - 1) // BATCH_SIZE + 1}...")

        try:
            result = classify_batch(client, batch, flat_nodes, model)
            for q in batch:
                node_id = result.get(q["id"])
                if node_id and node_id in valid_ids:
                    classified[q["id"]] = node_id
                else:
                    unclassified.append({
                        "id": q["id"],
                        "content": q["content"][:100],
                    })
        except Exception as e:
            print(f"    Error: {e}")
            for q in batch:
                unclassified.append({"id": q["id"], "content": q["content"][:100]})

    return {"classified": classified, "unclassified": unclassified}


def extract_tree_from_ts():
    """Extract tree structure from examTree.ts and save as JSON."""
    ts_path = PROJECT_ROOT / "src" / "data" / "examTree.ts"
    if not ts_path.exists():
        print(f"Error: {ts_path} not found")
        sys.exit(1)

    # Read the TypeScript file
    content = ts_path.read_text(encoding="utf-8")

    # Use a simple approach: find each subject's tree array
    # The tree data is essentially JSON-compatible if we strip TS syntax
    result = {}
    for sid in SUBJECTS:
        # Find tree: [...] for each subject
        # We look for the pattern: id: "sX", ... tree: [
        pattern = rf'id:\s*"{sid}".*?tree:\s*\['
        match = re.search(pattern, content, re.DOTALL)
        if not match:
            continue

        # Find the matching closing bracket
        start = match.end() - 1  # position of opening [
        depth = 0
        end = start
        for j in range(start, len(content)):
            if content[j] == "[":
                depth += 1
            elif content[j] == "]":
                depth -= 1
                if depth == 0:
                    end = j + 1
                    break

        tree_str = content[start:end]
        # Convert TS object syntax to JSON
        # Remove trailing commas
        tree_str = re.sub(r",\s*([}\]])", r"\1", tree_str)
        # Quote unquoted keys
        tree_str = re.sub(r"(\w+)\s*:", r'"\1":', tree_str)
        # Remove duplicate quotes on already-quoted keys
        tree_str = re.sub(r'"+"', '"', tree_str)

        try:
            tree_data = json.loads(tree_str)
            result[sid] = tree_data
            print(f"  {sid}: {len(tree_data)} top-level nodes")
        except json.JSONDecodeError as e:
            print(f"  {sid}: parse error: {e}")

    return result


def main():
    parser = argparse.ArgumentParser(description="Classify questions to tree nodes")
    parser.add_argument("--subject", "-s", help="Process single subject (e.g., s1)")
    parser.add_argument("--dry-run", action="store_true", help="Don't call GPT")
    parser.add_argument("--extract-tree", action="store_true", help="Extract tree from TS only")
    parser.add_argument("--model", default="gpt-4o-mini", help="GPT model to use")
    args = parser.parse_args()

    if args.extract_tree:
        print("Extracting tree from examTree.ts...")
        tree_data = extract_tree_from_ts()
        TREE_JSON.parent.mkdir(parents=True, exist_ok=True)
        TREE_JSON.write_text(
            json.dumps(tree_data, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        print(f"Saved to {TREE_JSON}")
        return

    if not TREE_JSON.exists():
        print("exam_tree.json not found, extracting from examTree.ts first...")
        tree_data = extract_tree_from_ts()
        TREE_JSON.parent.mkdir(parents=True, exist_ok=True)
        TREE_JSON.write_text(
            json.dumps(tree_data, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )

    subjects = [args.subject] if args.subject else SUBJECTS

    for sid in subjects:
        print(f"\nClassifying {sid}...")
        result = classify_subject(sid, dry_run=args.dry_run, model=args.model)

        # Save result
        out_dir = FRONTEND_DATA / sid
        out_dir.mkdir(parents=True, exist_ok=True)
        out_path = out_dir / "question_tree_map.json"
        out_path.write_text(
            json.dumps(result, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        print(f"  Saved: {out_path}")
        print(f"  Classified: {len(result['classified'])}, Unclassified: {len(result['unclassified'])}")


if __name__ == "__main__":
    main()
