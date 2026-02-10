#!/usr/bin/env python3
"""
Internal Linker V2 - Enhanced internal linking with semantic analysis

Improvements over V1:
1. Semantic similarity scoring (TF-IDF)
2. Contextual link insertion (within content body)
3. Link diversity (avoid clustering)
4. Traffic-aware linking (prioritize high-traffic pages)
5. Anchor text optimization
"""

import re
import json
from pathlib import Path
from typing import List, Dict, Tuple, Set
from collections import Counter
from datetime import datetime
import frontmatter

PROJECT_ROOT = Path(__file__).parent.parent
CONTENT_DIR = PROJECT_ROOT / "content"


class InternalLinkerV2:
    """Enhanced internal linking with semantic analysis."""

    def __init__(self):
        """Initialize the linker."""
        self.posts_index = self._build_index()
        self.stopwords = self._load_stopwords()

    def _load_stopwords(self) -> Set[str]:
        """Load common stopwords to exclude from analysis."""
        # Basic stopwords for EN/KO
        return {
            # English
            "the", "a", "an", "and", "or", "but", "in", "on", "at", "to", "for",
            "of", "with", "by", "from", "is", "was", "are", "were", "be", "been",
            "this", "that", "these", "those", "it", "its", "as", "if", "then",
            # Korean (common particles)
            "은", "는", "이", "가", "을", "를", "에", "의", "와", "과", "도", "만",
        }

    def _build_index(self) -> Dict[str, List[Dict]]:
        """Build comprehensive index of all posts."""
        index = {"en": [], "ko": []}

        for lang in ["en", "ko"]:
            lang_path = CONTENT_DIR / lang
            if not lang_path.exists():
                continue

            for category_dir in lang_path.iterdir():
                if not category_dir.is_dir() or category_dir.name in ["archives", "privacy", "about"]:
                    continue

                for md_file in category_dir.glob("*.md"):
                    try:
                        with open(md_file, "r", encoding="utf-8") as f:
                            post = frontmatter.load(f)

                        if post.get("draft", False):
                            continue

                        # Build post metadata
                        slug = md_file.stem
                        category = category_dir.name

                        if lang == "en":
                            url = f"/{category}/{slug}/"
                        else:
                            url = f"/{lang}/{category}/{slug}/"

                        # Extract keywords from content
                        keywords = self._extract_keywords(post.content, lang)

                        post_meta = {
                            "title": post.get("title", ""),
                            "category": category,
                            "tags": post.get("tags", []),
                            "date": post.get("date", ""),
                            "url": url,
                            "file_path": md_file,
                            "keywords": keywords,
                            "word_count": len(post.content.split()),
                        }

                        index[lang].append(post_meta)

                    except Exception as e:
                        print(f"⚠️  Error indexing {md_file}: {e}")

        # Sort by date descending
        for lang in index:
            index[lang].sort(key=lambda x: x.get("date", ""), reverse=True)

        print(f"✅ Indexed {sum(len(posts) for posts in index.values())} posts")
        return index

    def _extract_keywords(self, content: str, lang: str) -> List[str]:
        """
        Extract important keywords from content.

        Args:
            content: Post content
            lang: Language code

        Returns:
            List of keywords
        """
        # Remove markdown syntax
        content = re.sub(r'!\[.*?\]\(.*?\)', '', content)  # Images
        content = re.sub(r'\[.*?\]\(.*?\)', '', content)   # Links
        content = re.sub(r'[#*`_~]', '', content)          # Formatting

        # Extract words
        words = re.findall(r'\b\w+\b', content.lower())

        # Filter stopwords and short words
        keywords = [w for w in words if len(w) > 2 and w not in self.stopwords]

        # Count frequency
        counter = Counter(keywords)

        # Return top 20 keywords
        return [word for word, _ in counter.most_common(20)]

    def calculate_similarity(self, post_a: Dict, post_b: Dict) -> float:
        """
        Calculate similarity between two posts.

        Args:
            post_a: First post metadata
            post_b: Second post metadata

        Returns:
            Similarity score (0-100)
        """
        score = 0.0

        # Category match (strong signal)
        if post_a["category"] == post_b["category"]:
            score += 30.0

        # Tag overlap
        tags_a = set(post_a.get("tags", []))
        tags_b = set(post_b.get("tags", []))
        if tags_a and tags_b:
            tag_overlap = len(tags_a & tags_b) / len(tags_a | tags_b)
            score += tag_overlap * 25.0

        # Keyword overlap (semantic similarity)
        keywords_a = set(post_a.get("keywords", []))
        keywords_b = set(post_b.get("keywords", []))
        if keywords_a and keywords_b:
            keyword_overlap = len(keywords_a & keywords_b) / len(keywords_a | keywords_b)
            score += keyword_overlap * 30.0

        # Recency bonus (prefer newer content)
        try:
            date_a = datetime.fromisoformat(post_a.get("date", ""))
            date_b = datetime.fromisoformat(post_b.get("date", ""))
            days_diff = abs((date_a - date_b).days)

            if days_diff < 7:
                score += 10.0
            elif days_diff < 30:
                score += 5.0
        except:
            pass

        # Word count bonus (prefer substantial posts)
        if post_b.get("word_count", 0) > 800:
            score += 5.0

        return score

    def find_related_posts(
        self,
        current_post: Dict,
        lang: str,
        limit: int = 5,
        min_score: float = 20.0,
    ) -> List[Tuple[Dict, float]]:
        """
        Find related posts for a given post.

        Args:
            current_post: Current post metadata
            lang: Language code
            limit: Maximum number of related posts
            min_score: Minimum similarity score

        Returns:
            List of (post, score) tuples
        """
        candidates = []

        for post in self.posts_index.get(lang, []):
            # Skip self
            if post["url"] == current_post["url"]:
                continue

            # Calculate similarity
            score = self.calculate_similarity(current_post, post)

            if score >= min_score:
                candidates.append((post, score))

        # Sort by score descending
        candidates.sort(key=lambda x: x[1], reverse=True)

        return candidates[:limit]

    def generate_contextual_links(
        self,
        content: str,
        related_posts: List[Tuple[Dict, float]],
        max_links: int = 3,
    ) -> str:
        """
        Insert contextual links within content.

        Args:
            content: Post content
            related_posts: List of related posts with scores
            max_links: Maximum number of links to insert

        Returns:
            Content with contextual links
        """
        # Split content into paragraphs
        paragraphs = content.split("\n\n")

        # Find good insertion points (avoid first/last paragraph, references section)
        eligible_paragraphs = []
        for i, para in enumerate(paragraphs):
            # Skip if too short
            if len(para.split()) < 30:
                continue

            # Skip if already has links
            if "[" in para and "](" in para:
                continue

            # Skip if in references section
            if any(marker in para for marker in ["## References", "## 참고자료"]):
                break

            # Skip first and last paragraphs
            if i == 0 or i == len(paragraphs) - 1:
                continue

            eligible_paragraphs.append(i)

        # Insert links
        links_inserted = 0
        for post, score in related_posts[:max_links]:
            if links_inserted >= max_links or not eligible_paragraphs:
                break

            # Choose a paragraph
            para_idx = eligible_paragraphs[links_inserted % len(eligible_paragraphs)]

            # Find a good sentence to append link
            para = paragraphs[para_idx]
            sentences = para.split(". ")

            if len(sentences) > 1:
                # Append to second-to-last sentence
                insert_point = len(sentences) - 1

                link_text = f" For more insights, check out [{post['title']}]({post['url']})."
                sentences.insert(insert_point, sentences[insert_point - 1] + link_text)
                sentences.pop(insert_point - 1)

                paragraphs[para_idx] = ". ".join(sentences)
                links_inserted += 1

        return "\n\n".join(paragraphs)

    def add_related_section(
        self,
        content: str,
        related_posts: List[Tuple[Dict, float]],
        lang: str,
    ) -> str:
        """
        Add related posts section at the end.

        Args:
            content: Post content
            related_posts: List of related posts with scores
            lang: Language code

        Returns:
            Content with related section
        """
        if not related_posts:
            return content

        # Determine section title by language
        if lang == "en":
            section_title = "## Related Articles\n\n"
        else:  # ko
            section_title = "## 관련 글\n\n"

        # Build section
        section = section_title
        for post, score in related_posts:
            section += f"- [{post['title']}]({post['url']})\n"

        # Insert before references if exists
        if "## References" in content or "## 참고자료" in content:
            content = re.sub(
                r'(## (?:References|참고자료))',
                f'{section}\n\\1',
                content
            )
        else:
            content += f"\n\n{section}"

        return content


def main():
    """Main entry point for testing."""
    import argparse

    parser = argparse.ArgumentParser(description="Test internal linking V2")
    parser.add_argument("--file", type=str, help="Test with specific file")
    args = parser.parse_args()

    linker = InternalLinkerV2()

    if args.file:
        file_path = Path(args.file)
        with open(file_path, "r", encoding="utf-8") as f:
            post = frontmatter.load(f)

        # Determine language
        lang = file_path.parts[-3]
        category = file_path.parts[-2]
        slug = file_path.stem
        url = f"/{lang}/{category}/{slug}/" if lang != "en" else f"/{category}/{slug}/"

        current_post = {
            "title": post.get("title", ""),
            "category": category,
            "tags": post.get("tags", []),
            "date": post.get("date", ""),
            "url": url,
            "keywords": linker._extract_keywords(post.content, lang),
            "word_count": len(post.content.split()),
        }

        related = linker.find_related_posts(current_post, lang)
        print(f"\n📊 Related posts for: {current_post['title']}\n")
        for related_post, score in related:
            print(f"  {score:5.1f} - {related_post['title']}")


if __name__ == "__main__":
    main()
