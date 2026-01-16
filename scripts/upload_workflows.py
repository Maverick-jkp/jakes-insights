#!/usr/bin/env python3
"""
Upload workflow files to GitHub via API

This script uploads the workflow YAML files directly to GitHub
to bypass the workflow scope permission issue.
"""

import os
import sys
import base64
import requests
from pathlib import Path


def get_github_token():
    """Get GitHub token from git credential helper"""
    # Try to get token from git config
    import subprocess

    try:
        # Get remote URL
        result = subprocess.run(
            ['git', 'config', '--get', 'remote.origin.url'],
            capture_output=True,
            text=True,
            check=True
        )
        remote_url = result.stdout.strip()

        # Extract repo info
        # Format: https://github.com/Maverick-jkp/jakes-tech-insights.git
        if 'github.com' in remote_url:
            parts = remote_url.replace('.git', '').split('/')
            owner = parts[-2]
            repo = parts[-1]

            print(f"Repository: {owner}/{repo}")

            # Ask user for token
            print("\nGitHub Personal Access Token needed (with 'workflow' scope)")
            print("Create one at: https://github.com/settings/tokens")
            print("Required scope: 'workflow'")
            token = input("\nEnter your GitHub token: ").strip()

            return token, owner, repo

    except Exception as e:
        print(f"Error getting repo info: {e}")
        sys.exit(1)


def create_or_update_file(token, owner, repo, filepath, content, message):
    """Create or update a file via GitHub API"""

    # Encode content to base64
    content_bytes = content.encode('utf-8')
    content_b64 = base64.b64encode(content_bytes).decode('utf-8')

    # GitHub API endpoint
    api_url = f"https://api.github.com/repos/{owner}/{repo}/contents/{filepath}"

    headers = {
        'Authorization': f'token {token}',
        'Accept': 'application/vnd.github.v3+json',
    }

    # Check if file exists
    response = requests.get(api_url, headers=headers)

    sha = None
    if response.status_code == 200:
        sha = response.json()['sha']
        print(f"  File exists, will update (sha: {sha[:7]})")

    # Create/update file
    data = {
        'message': message,
        'content': content_b64,
        'branch': 'main'
    }

    if sha:
        data['sha'] = sha

    response = requests.put(api_url, headers=headers, json=data)

    if response.status_code in [200, 201]:
        print(f"  ✅ Success: {filepath}")
        return True
    else:
        print(f"  ❌ Failed: {response.status_code}")
        print(f"  Response: {response.text}")
        return False


def main():
    # Get GitHub credentials
    token, owner, repo = get_github_token()

    # Read workflow files
    workflows_dir = Path('.github/workflows')

    workflows = {
        'daily-content.yml': 'feat: Add daily content generation workflow',
    }

    print(f"\n{'='*60}")
    print("  Uploading Workflow Files to GitHub")
    print(f"{'='*60}\n")

    success_count = 0

    for filename, commit_msg in workflows.items():
        filepath = workflows_dir / filename

        if not filepath.exists():
            print(f"⚠️  File not found: {filepath}")
            continue

        print(f"Uploading: {filename}")

        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()

        github_path = f".github/workflows/{filename}"

        if create_or_update_file(token, owner, repo, github_path, content, commit_msg):
            success_count += 1

        print()

    print(f"{'='*60}")
    print(f"  {success_count}/{len(workflows)} files uploaded successfully")
    print(f"{'='*60}\n")

    if success_count == len(workflows):
        print("✅ All workflow files uploaded!")
        print("\nNext steps:")
        print("1. Go to GitHub → Settings → Secrets → Actions")
        print("2. Add secret: ANTHROPIC_API_KEY")
        print("3. Go to Actions tab to run workflows")
    else:
        print("⚠️  Some files failed to upload")
        sys.exit(1)


if __name__ == "__main__":
    main()
