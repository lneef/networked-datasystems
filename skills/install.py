#!/usr/bin/env python3
"""Install the shared KB skill for Codex and Claude Code on this machine."""

import argparse
from pathlib import Path


SKILL_NAME = "consult-networked-data-systems"
SOURCE = Path(__file__).resolve().parent / SKILL_NAME


def install(user_root: Path, dry_run: bool = False) -> None:
    if not (SOURCE / "SKILL.md").is_file():
        raise SystemExit(f"Missing skill source: {SOURCE}")
    destinations = [
        user_root / ".agents" / "skills" / SKILL_NAME,
        user_root / ".claude" / "skills" / SKILL_NAME,
    ]
    pending = []
    # Check both destinations before making changes; never replace another skill.
    for destination in destinations:
        if destination.is_symlink() and destination.resolve() == SOURCE:
            print(f"Already installed: {destination}")
        elif destination.exists() or destination.is_symlink():
            raise SystemExit(f"Refusing to overwrite existing path: {destination}")
        else:
            pending.append(destination)
    for destination in pending:
        if dry_run:
            print(f"Would link: {destination} -> {SOURCE}")
        else:
            destination.parent.mkdir(parents=True, exist_ok=True)
            destination.symlink_to(SOURCE, target_is_directory=True)
            print(f"Installed: {destination} -> {SOURCE}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dry-run", action="store_true", help="Preview without changes")
    args = parser.parse_args()
    install(Path.home(), dry_run=args.dry_run)
