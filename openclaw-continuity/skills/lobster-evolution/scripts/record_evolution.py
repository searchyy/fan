#!/usr/bin/env python3
import argparse
from datetime import datetime
from pathlib import Path

WORKSPACE = Path('/home/fan/.openclaw/workspace')
MEMORY_DIR = WORKSPACE / 'memory'


def ensure_daily_file(day: str) -> Path:
    MEMORY_DIR.mkdir(parents=True, exist_ok=True)
    path = MEMORY_DIR / f'{day}.md'
    if not path.exists():
        path.write_text(f'# {day}\n\n', encoding='utf-8')
    return path


def main() -> None:
    parser = argparse.ArgumentParser(description='Append a compact evolution note to today\'s daily memory file.')
    parser.add_argument('note', help='Learning note to append')
    parser.add_argument('--kind', default='learning', help='Tag for the note, e.g. learning/workflow/fix/preference')
    parser.add_argument('--day', default=datetime.now().strftime('%Y-%m-%d'), help='Target day in YYYY-MM-DD format')
    args = parser.parse_args()

    path = ensure_daily_file(args.day)
    stamp = datetime.now().strftime('%H:%M')
    line = f'- [{args.kind}][{stamp}] {args.note}\n'
    with path.open('a', encoding='utf-8') as f:
        f.write(line)
    print(f'Appended to {path}: {line.strip()}')


if __name__ == '__main__':
    main()
