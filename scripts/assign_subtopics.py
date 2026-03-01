#!/usr/bin/env python3
"""
Retroactively assign subtopic tags to existing posts.

Reads each post's frontmatter, determines the subtopic from title + tags,
then adds/updates the subtopic:* tag in the tags list.

Usage:
    python scripts/assign_subtopics.py [--dry-run]
"""

import re
import sys
import json
import argparse
from pathlib import Path


# Mirror of generate_posts.py SUBTOPIC_KEYWORDS
SUBTOPIC_KEYWORDS = {
    "ai": [
        "ai", "artificial intelligence", "machine learning", "deep learning", "llm",
        "gpt", "claude", "gemini", "openai", "anthropic", "mistral", "llama",
        "chatgpt", "copilot", "generative", "neural", "transformer", "diffusion",
        "stable diffusion", "midjourney", "dall-e", "hugging face", "pytorch",
        "tensorflow", "inference", "rag", "embedding", "vector", "fine-tuning",
        "prompt", "agent", "multimodal", "vision model", "speech recognition",
    ],
    "security": [
        "security", "cybersecurity", "vulnerability", "exploit", "cve", "hack",
        "breach", "malware", "ransomware", "phishing", "zero-day", "encryption",
        "authentication", "oauth", "jwt", "ssl", "tls", "firewall", "soc",
        "penetration", "pentest", "infosec", "devsecops", "compliance", "gdpr",
        "supply chain attack", "social engineering", "insider threat",
    ],
    "devtools": [
        "devtools", "developer tools", "ide", "vscode", "cursor", "neovim",
        "github", "gitlab", "git", "ci/cd", "github actions", "docker",
        "kubernetes", "k8s", "terraform", "ansible", "jest", "pytest",
        "testing", "debugging", "lint", "formatter", "package manager",
        "npm", "pnpm", "bun", "cargo", "poetry", "uv", "mise",
        "cli", "terminal", "shell", "zsh", "bash", "scripting",
    ],
    "cloud": [
        "cloud", "aws", "azure", "gcp", "google cloud", "serverless", "lambda",
        "ec2", "s3", "cloudflare", "vercel", "netlify", "heroku", "render",
        "kubernetes", "container", "microservice", "infrastructure", "iaas",
        "paas", "saas", "multi-cloud", "hybrid cloud", "edge computing",
        "cdn", "load balancer", "auto scaling", "terraform", "pulumi",
    ],
    "data": [
        "data", "database", "sql", "nosql", "postgresql", "mysql", "mongodb",
        "redis", "elasticsearch", "analytics", "data science", "pandas",
        "spark", "hadoop", "kafka", "data pipeline", "etl", "warehouse",
        "snowflake", "bigquery", "dbt", "airflow", "grafana", "tableau",
        "data engineering", "data lakehouse", "real-time", "streaming",
    ],
    "web": [
        "web", "frontend", "backend", "fullstack", "react", "vue", "angular",
        "svelte", "next.js", "nuxt", "astro", "remix", "javascript", "typescript",
        "css", "html", "tailwind", "api", "rest", "graphql", "websocket",
        "seo", "performance", "core web vitals", "accessibility", "pwa",
        "browser", "chrome", "web assembly", "wasm",
    ],
    "mobile": [
        "mobile", "ios", "android", "swift", "kotlin", "react native",
        "flutter", "expo", "app store", "play store", "xcode", "android studio",
        "push notification", "deep link", "in-app", "mobile app",
    ],
}


def assign_subtopic(text: str) -> str:
    """Return subtopic slug based on text content."""
    text_lower = text.lower()
    scores = {s: 0 for s in SUBTOPIC_KEYWORDS}
    for subtopic, terms in SUBTOPIC_KEYWORDS.items():
        for term in terms:
            if term in text_lower:
                scores[subtopic] += len(term.split())
    best = max(scores, key=lambda s: scores[s])
    return best if scores[best] > 0 else "other"


def parse_frontmatter(content: str):
    """Return (frontmatter_dict_raw_lines, body) by parsing YAML frontmatter."""
    if not content.startswith("---"):
        return None, content
    end = content.find("\n---", 3)
    if end == -1:
        return None, content
    fm_block = content[3:end].strip()
    body = content[end + 4:]
    return fm_block, body


def update_tags_in_frontmatter(fm_block: str, subtopic: str) -> str:
    """
    Replace or insert a subtopic:* tag inside the YAML tags line.
    Handles both inline `tags: ["a", "b"]` and multiline `tags:\n  - a` formats.
    """
    subtopic_tag = f"subtopic:{subtopic}"

    # Remove any existing subtopic:* tag
    # Inline JSON array format: tags: ["foo", "subtopic:bar", "baz"]
    def replace_in_json_array(m):
        raw = m.group(0)
        try:
            # extract the JSON array
            arr_match = re.search(r'\[.*\]', raw, re.DOTALL)
            if not arr_match:
                return raw
            arr = json.loads(arr_match.group(0))
            arr = [t for t in arr if not t.startswith("subtopic:")]
            arr.append(subtopic_tag)
            arr_str = json.dumps(arr, ensure_ascii=False)
            return raw[:arr_match.start()] + arr_str + raw[arr_match.end():]
        except Exception:
            return raw

    # Try inline JSON array first
    if re.search(r'^tags:\s*\[', fm_block, re.MULTILINE):
        new_fm = re.sub(r'^tags:\s*\[.*?\]', replace_in_json_array, fm_block, flags=re.MULTILINE | re.DOTALL)
        return new_fm

    # Try YAML list (multiline)
    if re.search(r'^tags:', fm_block, re.MULTILINE):
        lines = fm_block.split('\n')
        in_tags = False
        new_lines = []
        has_subtopic = False
        for line in lines:
            if re.match(r'^tags:', line):
                in_tags = True
                new_lines.append(line)
                continue
            if in_tags:
                if re.match(r'^\s+-\s+', line):
                    tag_val = re.sub(r'^\s+-\s+["\']?', '', line).rstrip("\"'")
                    if tag_val.startswith("subtopic:"):
                        # Replace with new subtopic
                        new_lines.append(re.sub(r'subtopic:\S+', subtopic_tag, line))
                        has_subtopic = True
                        continue
                    new_lines.append(line)
                else:
                    # End of tags block — insert subtopic if not yet added
                    if not has_subtopic:
                        new_lines.append(f'  - "{subtopic_tag}"')
                        has_subtopic = True
                    in_tags = False
                    new_lines.append(line)
            else:
                new_lines.append(line)
        if in_tags and not has_subtopic:
            new_lines.append(f'  - "{subtopic_tag}"')
        return '\n'.join(new_lines)

    # No tags field — append one
    return fm_block + f'\ntags: ["{subtopic_tag}"]'


def process_file(path: Path, dry_run: bool) -> bool:
    """Process a single post file. Returns True if modified."""
    content = path.read_text(encoding='utf-8')
    fm_block, body = parse_frontmatter(content)
    if fm_block is None:
        return False

    # Build search text: title + existing tags
    title_match = re.search(r'^title:\s*["\']?(.*?)["\']?\s*$', fm_block, re.MULTILINE)
    title = title_match.group(1) if title_match else ""

    # Also grab existing tags text for scoring
    existing_tags = re.findall(r'"([^"]+)"', fm_block)
    search_text = title + " " + " ".join(existing_tags)

    # Check if subtopic already assigned
    current_subtopic = None
    for tag in existing_tags:
        if tag.startswith("subtopic:"):
            current_subtopic = tag.replace("subtopic:", "")
            break

    subtopic = assign_subtopic(search_text)

    if current_subtopic == subtopic:
        return False  # Already correct

    new_fm = update_tags_in_frontmatter(fm_block, subtopic)
    new_content = f"---\n{new_fm}\n---{body}"

    if not dry_run:
        path.write_text(new_content, encoding='utf-8')

    print(f"{'[DRY RUN] ' if dry_run else ''}{'Updated' if current_subtopic else 'Tagged'}: {path.name} → {subtopic}")
    return True


def main():
    parser = argparse.ArgumentParser(description="Assign subtopic tags to existing posts")
    parser.add_argument("--dry-run", action="store_true", help="Preview changes without writing")
    args = parser.parse_args()

    root = Path(__file__).parent.parent
    content_dirs = [root / "content" / "en", root / "content" / "ko"]

    total = 0
    modified = 0

    # Skip these page-type filenames (not blog posts)
    skip_names = {"about.md", "contact.md", "privacy.md", "all-posts.md", "_index.md"}

    for content_dir in content_dirs:
        if not content_dir.exists():
            continue
        for md_file in sorted(content_dir.rglob("*.md")):
            if md_file.name in skip_names:
                continue
            total += 1
            if process_file(md_file, args.dry_run):
                modified += 1

    print(f"\nDone: {modified}/{total} files {'would be ' if args.dry_run else ''}updated.")


if __name__ == "__main__":
    main()
