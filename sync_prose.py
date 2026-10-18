"""Copy the prose checker files of narrative-python into skill/, byte for byte.

narrative-java runs the prose checks of narrative-python unchanged, so the five files in COPIED_FILES
are copies. Each copy writes skill/PROSE_SOURCE, with a path= line and a commit= line for the
narrative-python checkout they came from. The file is local, and git ignores it. Without it, the
checkout is ../improved-ai-code-style.

With --check, nothing is copied, and a copy that differs from its source is an error.

Usage:
    $ python3 sync_prose.py
    $ python3 sync_prose.py ~/src/narrative-python
    $ python3 sync_prose.py --check

Exit codes:
    0  every file was copied, or every copy matches its source
    1  --check found a copy that differs from its source
    2  the narrative-python checkout, or a file in it, is missing
"""

from __future__ import annotations

import argparse
import filecmp
import shutil
import subprocess
import sys
from pathlib import Path


COPIED_FILES = ('checks.py', 'agentverbs.py', 'prose.py', 'words.json', 'requirements-lock.txt')
REPO_DIR = Path(__file__).resolve().parent
TARGET_SKILL_DIR = REPO_DIR / 'skill'
SOURCE_RECORD_PATH = TARGET_SKILL_DIR / 'PROSE_SOURCE'
DEFAULT_SOURCE_DIR = REPO_DIR.parent / 'improved-ai-code-style'
EXIT_SUCCESS = 0
EXIT_DIFFERS = 1
EXIT_NO_SOURCE = 2


def main() -> int:
    """Copy COPIED_FILES into skill/ and write skill/PROSE_SOURCE, or with --check compare them."""
    parser = argparse.ArgumentParser(description='Copy the prose checker files of narrative-python into skill/.')
    parser.add_argument(
        'source_dir',
        nargs='?',
        type=Path,
        help='the narrative-python checkout (default: the path in skill/PROSE_SOURCE, else ../improved-ai-code-style)',
    )
    parser.add_argument('--check', action='store_true', help='copy nothing, and exit 1 if a copy differs')
    args = parser.parse_args()
    source_skill_dir = (args.source_dir or readRecordedSourceDir()) / 'skill'

    missing = [name for name in COPIED_FILES if not (source_skill_dir / name).is_file()]
    if missing:
        print(
            f'sync_prose.py: {", ".join(missing)} not in {source_skill_dir}. '
            'Pass the narrative-python checkout as the first argument',
            file=sys.stderr,
        )
        return EXIT_NO_SOURCE

    if args.check:
        differing = listDifferingCopies(source_skill_dir)
        for name in differing:
            print(f'sync_prose.py: skill/{name} differs from {source_skill_dir / name}', file=sys.stderr)
        return EXIT_DIFFERS if differing else EXIT_SUCCESS

    for name in COPIED_FILES:
        shutil.copyfile(source_skill_dir / name, TARGET_SKILL_DIR / name)
    commit = readSourceCommit(source_skill_dir.parent)
    SOURCE_RECORD_PATH.write_text(f'path={source_skill_dir.parent.resolve()}\ncommit={commit}\n', encoding='utf-8')
    print(f'copied {len(COPIED_FILES)} files from {source_skill_dir}, commit {commit}')
    return EXIT_SUCCESS


def readRecordedSourceDir() -> Path:
    """Return the checkout named on the path= line of skill/PROSE_SOURCE, or DEFAULT_SOURCE_DIR."""
    if not SOURCE_RECORD_PATH.is_file():
        return DEFAULT_SOURCE_DIR

    for line in SOURCE_RECORD_PATH.read_text(encoding='utf-8').splitlines():
        if line.startswith('path='):
            return Path(line.removeprefix('path='))
    return DEFAULT_SOURCE_DIR


def listDifferingCopies(source_skill_dir: Path) -> list[str]:
    return [
        name
        for name in COPIED_FILES
        if not (TARGET_SKILL_DIR / name).is_file()
        or not filecmp.cmp(source_skill_dir / name, TARGET_SKILL_DIR / name, shallow=False)
    ]


def readSourceCommit(source_dir: Path) -> str:
    """Return the short commit of the checkout, with a suffix when its skill/ has uncommitted changes."""
    head = subprocess.run(
        ['git', '-C', str(source_dir), 'rev-parse', '--short', 'HEAD'],
        capture_output=True,
        text=True,
        check=False,
    )
    if head.returncode != 0:
        return 'unknown commit'

    status = subprocess.run(
        ['git', '-C', str(source_dir), 'status', '--porcelain', '--', 'skill'],
        capture_output=True,
        text=True,
        check=False,
    )
    suffix = ' with uncommitted changes' if status.stdout.strip() else ''
    return head.stdout.strip() + suffix


if __name__ == '__main__':
    sys.exit(main())
