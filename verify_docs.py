"""Check the docs of narrative-java against the decision records, the rule codes and the copied files.

- Every record of benchmark/decisions.jsonl matches the schema of narrative-python, with the round
  `j1`.
- Every decision id cited in a Markdown file resolves: a `J1-` id in benchmark/decisions.jsonl here,
  every other id in benchmark/decisions.jsonl of the narrative-python checkout named in
  skill/PROSE_SOURCE. A doc that states the current rules (skill/ and README.md) cites no superseded
  id.
- Every NAR code named in a Markdown file is a code of checks.py, agentverbs.py, javachecks.py or
  pmd-ruleset.xml.
- The five files that sync_prose.py copies are the same, byte for byte, as their source.

Usage:
    $ python3 verify_docs.py

Exit codes:
    0  no problem
    1  at least one problem
    2  the narrative-python checkout of skill/PROSE_SOURCE is missing
"""

from __future__ import annotations

import ast
import filecmp
import json
import re
import sys
from pathlib import Path


REPO_DIR = Path(__file__).resolve().parent
SKILL_DIR = REPO_DIR / 'skill'
COPIED_FILES = ('checks.py', 'agentverbs.py', 'prose.py', 'words.json', 'requirements-lock.txt')
DECISION_FIELDS = ('id', 'dimension', 'round', 'kind', 'options', 'choice', 'strength', 'condition', 'note', 'date')
DECISION_ROUNDS = frozenset({'j1'})
DECISION_KINDS = frozenset({'control', 'gap', 'provocation', 'derived'})
DECISION_STRENGTHS = frozenset({'strong', 'weak'})
NULLABLE_FIELDS = frozenset({'condition', 'note', 'strength'})
LIST_FIELDS = frozenset({'options', 'supersedes'})
SKIPPED_DIRS = frozenset({'.git', '.gradle', 'build', '.lintenv'})
EXIT_SUCCESS = 0
EXIT_PROBLEMS = 1
EXIT_NO_SOURCE = 2


def main() -> int:
    """Run the four checks and print every problem."""
    # matches:
    # `R10-fence-form`  # noqa: NAR012
    # `J1-P31b`
    # `Q08`  # noqa: NAR012
    # `V-03`  # noqa: NAR012
    # rejects:
    # `Q8`
    DECISION_ID = re.compile(
        r'\b(?:J1-[A-Za-z0-9]+(?:-[A-Za-z0-9]+)*|Q\d{2}|R\d{1,2}[a-z]?-[A-Za-z0-9]+(?:-[A-Za-z0-9]+)*|V-\d\d)\b',
    )
    source_dir = readSourceDir()
    python_decisions_path = source_dir / 'benchmark' / 'decisions.jsonl'
    if not python_decisions_path.is_file():
        print(f'verify_docs.py: no {python_decisions_path}. Run sync_prose.py with the narrative-python checkout')
        return EXIT_NO_SOURCE

    java_decisions = readDecisions(REPO_DIR / 'benchmark' / 'decisions.jsonl')
    python_decisions = readDecisions(python_decisions_path)
    problems = schemaProblems(java_decisions)
    java_ids = {str(record['id']) for record in java_decisions}
    python_ids = {str(record['id']) for record in python_decisions}
    replaced = {old: str(record['id']) for record in python_decisions for old in supersededIds(record)}
    codes = readRuleCodes()

    documents = sorted(path for path in REPO_DIR.rglob('*.md') if not SKIPPED_DIRS & set(path.parts))
    citations = 0
    for document in documents:
        relative = document.relative_to(REPO_DIR)
        text = document.read_text(encoding='utf-8')
        current = relative.parts[0] == 'skill' or relative.as_posix() == 'README.md'
        for cited in DECISION_ID.findall(text):
            citations += 1
            known = java_ids if cited.startswith('J1-') else python_ids
            if cited not in known:
                problems.append(f'{relative}: cites unknown decision {cited}')
            elif current and cited in replaced:
                problems.append(f'{relative}: cites {cited}, which {replaced[cited]} superseded')
        problems.extend(
            f'{relative}: names unknown rule {code}' for code in sorted(set(re.findall(r'\bNAR\d{3}\b', text)) - codes)
        )

    for name in COPIED_FILES:
        if not filecmp.cmp(source_dir / 'skill' / name, SKILL_DIR / name, shallow=False):
            problems.append(f'skill/{name} differs from {source_dir / "skill" / name}. Run sync_prose.py')

    print(f'checked {len(documents)} documents, {citations} decision citations, {len(codes)} rule codes')
    print(f'decisions: {len(java_ids)} here, {len(python_ids)} in {python_decisions_path}')
    for problem in problems:
        print(f'  PROBLEM  {problem}')
    print(f'{len(problems)} problems')
    return EXIT_PROBLEMS if problems else EXIT_SUCCESS


def readSourceDir() -> Path:
    """Return the narrative-python checkout named on the path= line of skill/PROSE_SOURCE."""
    for line in (SKILL_DIR / 'PROSE_SOURCE').read_text(encoding='utf-8').splitlines():
        if line.startswith('path='):
            return Path(line.removeprefix('path='))
    return REPO_DIR.parent / 'improved-ai-code-style'


def supersededIds(record: dict[str, object]) -> list[str]:
    value = record.get('supersedes')
    return [str(item) for item in value] if isinstance(value, list) else []


def readDecisions(decisions_path: Path) -> list[dict[str, object]]:
    return [json.loads(line) for line in decisions_path.read_text(encoding='utf-8').splitlines() if line.strip()]


def schemaProblems(decisions: list[dict[str, object]]) -> list[str]:
    """Report every J1 record that does not match the schema of narrative-python."""
    problems: list[str] = []
    seen: set[str] = set()
    for record in decisions:
        name = str(record.get('id', '<no id>'))
        if name in seen:
            problems.append(f'decisions.jsonl {name}: duplicate id')
        seen.add(name)
        fields = tuple(record)
        if fields[: len(DECISION_FIELDS)] != DECISION_FIELDS or not set(fields[len(DECISION_FIELDS) :]) <= {
            'supersedes',
        }:
            problems.append(f'decisions.jsonl {name}: fields are {fields}, schema says {DECISION_FIELDS}')
            continue

        for field, value in record.items():
            if value is None and field not in NULLABLE_FIELDS:
                problems.append(f'decisions.jsonl {name}: {field} is null and the schema does not allow it')
            elif field in LIST_FIELDS and not (
                isinstance(value, list) and all(isinstance(item, str) for item in value)
            ):
                problems.append(f'decisions.jsonl {name}: {field} is not a list of strings')
            elif field not in LIST_FIELDS and value is not None and not isinstance(value, str):
                problems.append(f'decisions.jsonl {name}: {field} is {type(value).__name__}, schema says str')
        for field, allowed in (('round', DECISION_ROUNDS), ('kind', DECISION_KINDS), ('strength', DECISION_STRENGTHS)):
            if record[field] is not None and record[field] not in allowed:
                problems.append(f'decisions.jsonl {name}: {field} is {record[field]!r}, not one of {sorted(allowed)}')
    return problems


def readRuleCodes() -> set[str]:
    """Collect every NAR code of the checks of narrative-java, and the codes retired in checks.py.

    The codes are the RULES and RETIRED keys of checks.py, the CODE, FRAGMENT_CODE and CONNECTIVE_CODE
    constants of agentverbs.py, and every NAR code in the text of javachecks.py and pmd-ruleset.xml.
    """
    codes: set[str] = set()
    for node in ast.parse((SKILL_DIR / 'checks.py').read_text(encoding='utf-8')).body:
        registry = isinstance(node, ast.Assign) and getattr(node.targets[0], 'id', '') in {'RULES', 'RETIRED'}
        if registry and isinstance(node, ast.Assign) and isinstance(node.value, ast.Dict):
            codes.update(
                key.value for key in node.value.keys if isinstance(key, ast.Constant) and isinstance(key.value, str)
            )
    for node in ast.parse((SKILL_DIR / 'agentverbs.py').read_text(encoding='utf-8')).body:
        names = {'CODE', 'FRAGMENT_CODE', 'CONNECTIVE_CODE'}
        constant = isinstance(node, ast.Assign) and getattr(node.targets[0], 'id', '') in names
        if constant and isinstance(node, ast.Assign) and isinstance(node.value, ast.Constant):
            codes.add(str(node.value.value))
    for name in ('javachecks.py', 'pmd-ruleset.xml'):
        codes.update(re.findall(r'\bNAR\d{3}\b', (SKILL_DIR / name).read_text(encoding='utf-8')))
    return codes


if __name__ == '__main__':
    sys.exit(main())
