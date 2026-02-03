#!/usr/bin/env python3
"""
Topic Cluster Manager
Manages pillar content and supporting posts for SEO topic clusters
"""

import json
import os
from pathlib import Path
from typing import Dict, List, Optional, Tuple
import re


class ClusterManager:
    """Manages topic clusters and pillar content relationships"""

    def __init__(self, clusters_file: str = "data/topic_clusters.json"):
        self.clusters_file = Path(clusters_file)
        self.clusters = self.load_clusters()

    def load_clusters(self) -> Dict:
        """Load cluster data from JSON file"""
        if not self.clusters_file.exists():
            print(f"Warning: Clusters file not found at {self.clusters_file}")
            return {}

        try:
            with open(self.clusters_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except json.JSONDecodeError as e:
            print(f"Error loading clusters file: {e}")
            return {}

    def save_clusters(self) -> None:
        """Save cluster data to JSON file"""
        with open(self.clusters_file, 'w', encoding='utf-8') as f:
            json.dump(self.clusters, f, indent=2, ensure_ascii=False)

    def find_cluster(self, category: str, tags: List[str]) -> Optional[Tuple[str, str]]:
        """
        Find the best matching cluster for a post

        Args:
            category: Post category (e.g., 'tech', 'business')
            tags: List of post tags

        Returns:
            Tuple of (category, cluster_id) or None if no match
        """
        if category not in self.clusters:
            return None

        # Normalize category to lowercase
        category = category.lower()

        # Try to match based on tags and cluster keywords
        best_match = None
        best_score = 0

        for cluster_id, cluster_data in self.clusters[category].items():
            pillar = cluster_data.get('pillar', {})
            keywords = pillar.get('target_keywords', [])

            # Calculate match score
            score = 0
            for tag in tags:
                tag_lower = tag.lower()
                for keyword in keywords:
                    keyword_lower = keyword.lower()
                    # Exact match
                    if tag_lower == keyword_lower:
                        score += 10
                    # Partial match
                    elif tag_lower in keyword_lower or keyword_lower in tag_lower:
                        score += 5

            if score > best_score:
                best_score = score
                best_match = (category, cluster_id)

        # Return match only if score is significant
        return best_match if best_score >= 5 else None

    def link_to_pillar(self, post_path: str, category: str, cluster_id: str) -> bool:
        """
        Add pillar content link to a post

        Args:
            post_path: Path to the post markdown file
            category: Category of the cluster
            cluster_id: ID of the cluster

        Returns:
            True if link was added successfully
        """
        if category not in self.clusters or cluster_id not in self.clusters[category]:
            print(f"Warning: Cluster {category}/{cluster_id} not found")
            return False

        post_file = Path(post_path)
        if not post_file.exists():
            print(f"Warning: Post file not found at {post_path}")
            return False

        # Read the post content
        with open(post_file, 'r', encoding='utf-8') as f:
            content = f.read()

        # Check if pillar link already exists
        if '## Related Resources' in content or '## 관련 자료' in content or '## 関連リソース' in content:
            print(f"Pillar link section already exists in {post_path}")
            return False

        # Get pillar info
        pillar = self.clusters[category][cluster_id]['pillar']
        pillar_title = pillar['title']

        # Determine language from path
        if '/en/' in str(post_path):
            lang = 'en'
            section_title = "## Related Resources"
            link_text = f"📚 For a comprehensive guide, see: [{pillar_title}](/pillar/{category}/{cluster_id}/)"
        elif '/ko/' in str(post_path):
            lang = 'ko'
            section_title = "## 관련 자료"
            link_text = f"📚 전체 가이드: [{pillar_title}](/pillar/{category}/{cluster_id}/)"
        elif '/ja/' in str(post_path):
            lang = 'ja'
            section_title = "## 関連リソース"
            link_text = f"📚 完全ガイド: [{pillar_title}](/pillar/{category}/{cluster_id}/)"
        else:
            print(f"Warning: Could not determine language for {post_path}")
            return False

        # Add pillar link before the final section (usually "Conclusion" or similar)
        # Insert before the last ## heading
        lines = content.split('\n')
        last_heading_idx = -1

        for i in range(len(lines) - 1, -1, -1):
            if lines[i].startswith('## '):
                last_heading_idx = i
                break

        if last_heading_idx > 0:
            # Insert before last heading
            lines.insert(last_heading_idx, '')
            lines.insert(last_heading_idx, link_text)
            lines.insert(last_heading_idx, section_title)
            lines.insert(last_heading_idx, '')
        else:
            # Append to end
            lines.append('')
            lines.append(section_title)
            lines.append('')
            lines.append(link_text)

        # Write back
        with open(post_file, 'w', encoding='utf-8') as f:
            f.write('\n'.join(lines))

        print(f"✓ Added pillar link to {post_path}")
        return True

    def update_cluster_index(self, category: str, cluster_id: str, post_info: Dict) -> None:
        """
        Add a supporting post to the cluster index

        Args:
            category: Category of the cluster
            cluster_id: ID of the cluster
            post_info: Dictionary with post metadata (title, path, date, etc.)
        """
        if category not in self.clusters or cluster_id not in self.clusters[category]:
            print(f"Warning: Cluster {category}/{cluster_id} not found")
            return

        supporting_posts = self.clusters[category][cluster_id].get('supporting_posts', [])

        # Check if post already exists
        for post in supporting_posts:
            if post.get('path') == post_info.get('path'):
                print(f"Post already in cluster: {post_info.get('path')}")
                return

        # Add post
        supporting_posts.append(post_info)
        self.clusters[category][cluster_id]['supporting_posts'] = supporting_posts

        # Save
        self.save_clusters()
        print(f"✓ Added post to cluster {category}/{cluster_id}")

    def get_cluster_stats(self) -> Dict:
        """Get statistics about all clusters"""
        stats = {}

        for category, clusters in self.clusters.items():
            stats[category] = {}
            for cluster_id, cluster_data in clusters.items():
                supporting_count = len(cluster_data.get('supporting_posts', []))
                pillar_status = cluster_data.get('pillar', {}).get('status', 'unknown')

                stats[category][cluster_id] = {
                    'pillar_status': pillar_status,
                    'supporting_posts': supporting_count
                }

        return stats

    def print_cluster_stats(self) -> None:
        """Print cluster statistics in a readable format"""
        stats = self.get_cluster_stats()

        print("\n=== Topic Cluster Statistics ===\n")

        for category, clusters in stats.items():
            print(f"📁 {category.upper()}")
            for cluster_id, data in clusters.items():
                status_emoji = "✓" if data['pillar_status'] == 'published' else "○"
                print(f"  {status_emoji} {cluster_id}: {data['supporting_posts']} supporting posts")
            print()


def main():
    """CLI interface for cluster management"""
    import argparse

    parser = argparse.ArgumentParser(description='Manage topic clusters')
    parser.add_argument('action', choices=['stats', 'link', 'find'],
                        help='Action to perform')
    parser.add_argument('--post', help='Post file path (for link action)')
    parser.add_argument('--category', help='Category (for link action)')
    parser.add_argument('--cluster', help='Cluster ID (for link action)')
    parser.add_argument('--tags', help='Comma-separated tags (for find action)')

    args = parser.parse_args()

    manager = ClusterManager()

    if args.action == 'stats':
        manager.print_cluster_stats()

    elif args.action == 'link':
        if not all([args.post, args.category, args.cluster]):
            print("Error: --post, --category, and --cluster are required for link action")
            return

        success = manager.link_to_pillar(args.post, args.category, args.cluster)
        if success:
            # Extract post info for cluster index
            post_path = Path(args.post)
            post_info = {
                'path': str(post_path),
                'title': post_path.stem,
                'added_date': str(Path(post_path).stat().st_mtime)
            }
            manager.update_cluster_index(args.category, args.cluster, post_info)

    elif args.action == 'find':
        if not all([args.category, args.tags]):
            print("Error: --category and --tags are required for find action")
            return

        tags = [t.strip() for t in args.tags.split(',')]
        result = manager.find_cluster(args.category, tags)

        if result:
            print(f"Best match: {result[0]}/{result[1]}")
        else:
            print("No matching cluster found")


if __name__ == '__main__':
    main()
