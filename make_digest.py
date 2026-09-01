from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parent
OUTPUT_FILE = ROOT / "digest.txt"

INCLUDED_EXTENSIONS = {
    ".css",
    ".env.example",
    ".html",
    ".ini",
    ".js",
    ".jsx",
    ".json",
    ".md",
    ".mjs",
    ".py",
    ".sql",
    ".toml",
    ".ts",
    ".tsx",
    ".yml",
    ".yaml",
}

INCLUDED_FILENAMES = {
    ".gitignore",
    "Dockerfile",
}

EXCLUDED_DIRS = {
    ".git",
    ".mypy_cache",
    ".next",
    ".pytest_cache",
    ".ruff_cache",
    ".turbo",
    ".venv",
    "__pycache__",
    "build",
    "coverage",
    "dist",
    "node_modules",
    "tmp-run-logs",
    "venv",
}

EXCLUDED_FILENAMES = {
    "digest.txt",
    "output.txt",
    "package-lock.json",
    "pnpm-lock.yaml",
    "yarn.lock",
    "tsconfig.tsbuildinfo",
    "uv.lock",
}


def should_include(path: Path) -> bool:
    relative = path.relative_to(ROOT)
    if any(part in EXCLUDED_DIRS for part in relative.parts):
        return False
    if path.name in EXCLUDED_FILENAMES:
        return False
    if path.name in INCLUDED_FILENAMES:
        return True
    return path.suffix in INCLUDED_EXTENSIONS


def read_text(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        return path.read_text(encoding="utf-8", errors="replace")


def main() -> None:
    files = sorted(
        path
        for path in ROOT.rglob("*")
        if path.is_file() and should_include(path)
    )

    lines: list[str] = [
        "# Project Code Digest",
        "",
        f"Root: {ROOT}",
        f"Files included: {len(files)}",
        "",
    ]

    for path in files:
        relative = path.relative_to(ROOT).as_posix()
        lines.extend(
            [
                "=" * 100,
                f"FILE: {relative}",
                "=" * 100,
                read_text(path).rstrip(),
                "",
            ]
        )

    OUTPUT_FILE.write_text("\n".join(lines), encoding="utf-8")
    print(f"Wrote {OUTPUT_FILE} with {len(files)} files.")


if __name__ == "__main__":
    main()
