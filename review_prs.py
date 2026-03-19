#!/usr/bin/env python3
"""
PR Intelligence Review Script
Runs each sample PR through Claude using REVIEW.md as the review guide.
"""

import anthropic
from pathlib import Path

# ── Config ────────────────────────────────────────────────────────────────────

REPO_ROOT = Path(__file__).parent
REVIEW_GUIDE = REPO_ROOT / "REVIEW.md"
SAMPLE_PR_DIR = REPO_ROOT / "sample_pr"
OUTPUT_DIR = REPO_ROOT / "sample_pr_claude_outputs"

PR_DIRS = [
    SAMPLE_PR_DIR / "open_onboarding_preview",
    SAMPLE_PR_DIR / "merged_add_user_email_domain",
    SAMPLE_PR_DIR / "open_blank_cleanup",
]

# ── Helpers ───────────────────────────────────────────────────────────────────

def read_file(path: Path) -> str:
    """Return file contents or a placeholder if the file is missing/empty."""
    if not path.exists():
        return "(file not found)"
    content = path.read_text().strip()
    return content if content else "(empty)"


def load_pr(pr_dir: Path) -> dict:
    return {
        "name": pr_dir.name,
        "metadata": read_file(pr_dir / "pr.md"),
        "diff":     read_file(pr_dir / "changes.diff"),
        "commits":  read_file(pr_dir / "commits.txt"),
    }


def build_prompt(review_guide: str, pr: dict) -> str:
    return f"""You are a senior engineer conducting a code review.
Use the review guide below as your standard — it defines what to check, \
coding style expectations, high-risk areas, and what to skip.

<review_guide>
{review_guide}
</review_guide>

Now review the following pull request.

## PR Metadata
{pr['metadata']}

## Commits
{pr['commits']}

## Diff
```diff
{pr['diff']}
```

Produce a structured review with these sections:
1. **Summary** — one-sentence description of what this PR does
2. **Risk Level** — Low / Medium / High, with a one-line reason
3. **Checklist** — go through the relevant items from the review guide; \
mark each ✅ (pass), ⚠️ (concern), or ❌ (fail), with a brief note
4. **Issues Found** — numbered list of concrete problems; \
include file:line references where possible
5. **Verdict** — Approve / Request Changes / Reject, with a one-sentence rationale

Be direct and specific. Skip boilerplate."""


def separator(title: str, width: int = 72) -> str:
    line = "─" * width
    pad = (width - len(title) - 2) // 2
    return f"\n{line}\n{' ' * pad} {title}\n{line}"


# ── Main ──────────────────────────────────────────────────────────────────────

def main():
    if not REVIEW_GUIDE.exists():
        raise FileNotFoundError(f"REVIEW.md not found at {REVIEW_GUIDE}")

    review_guide = REVIEW_GUIDE.read_text()
    client = anthropic.Anthropic()  # reads ANTHROPIC_API_KEY from env

    prs = [load_pr(d) for d in PR_DIRS if d.exists()]
    if not prs:
        print("No PR directories found under sample_pr/")
        return

    OUTPUT_DIR.mkdir(exist_ok=True)

    print(separator(f"PR INTELLIGENCE REVIEW  ({len(prs)} PRs)"))

    for i, pr in enumerate(prs, 1):
        print(separator(f"PR {i}/{len(prs)}: {pr['name']}"))
        prompt = build_prompt(review_guide, pr)

        print("Reviewing… ", end="", flush=True)

        chunks = []
        # Stream the response so long reviews appear incrementally
        with client.messages.stream(
            model="claude-opus-4-6",
            max_tokens=2048,
            thinking={"type": "adaptive"},
            messages=[{"role": "user", "content": prompt}],
        ) as stream:
            print()  # newline after "Reviewing…"
            for text in stream.text_stream:
                print(text, end="", flush=True)
                chunks.append(text)

        output_path = OUTPUT_DIR / f"{pr['name']}.md"
        output_path.write_text("".join(chunks))
        print(f"\n[Saved → {output_path.relative_to(REPO_ROOT)}]")

        print()  # blank line after each review

    print(separator("DONE"))


if __name__ == "__main__":
    main()
