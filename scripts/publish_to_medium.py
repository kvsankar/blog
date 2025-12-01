#!/usr/bin/env python3
"""
Cross-post Hugo blog posts to Medium.

Usage:
    python publish_to_medium.py <path_to_markdown_file>

Environment variables required:
    MEDIUM_TOKEN - Your Medium integration token
    MEDIUM_USER_ID - Your Medium user ID

To get these:
1. Go to https://medium.com/me/settings/security
2. Create an Integration Token
3. Get your user ID by calling: curl -H "Authorization: Bearer YOUR_TOKEN" https://api.medium.com/v1/me
"""

import os
import re
import sys
import argparse
import requests
from pathlib import Path


def get_medium_credentials():
    """Get Medium API credentials from environment."""
    token = os.environ.get("MEDIUM_TOKEN")
    user_id = os.environ.get("MEDIUM_USER_ID")

    if not token:
        print("Error: MEDIUM_TOKEN environment variable not set")
        print("Get your token at: https://medium.com/me/settings/security")
        sys.exit(1)

    if not user_id:
        # Try to fetch user ID using token
        print("MEDIUM_USER_ID not set, fetching from API...")
        response = requests.get(
            "https://api.medium.com/v1/me",
            headers={"Authorization": f"Bearer {token}"}
        )
        if response.status_code == 200:
            user_id = response.json()["data"]["id"]
            print(f"Your Medium user ID is: {user_id}")
            print("Set it as: export MEDIUM_USER_ID=" + user_id)
        else:
            print(f"Error fetching user ID: {response.text}")
            sys.exit(1)

    return token, user_id


def parse_front_matter(content):
    """Extract and remove YAML front matter from markdown."""
    front_matter = {}

    # Match YAML front matter
    match = re.match(r'^---\s*\n(.*?)\n---\s*\n', content, re.DOTALL)
    if match:
        yaml_content = match.group(1)
        # Simple YAML parsing for common fields
        for line in yaml_content.split('\n'):
            if ':' in line:
                key, value = line.split(':', 1)
                key = key.strip()
                value = value.strip().strip('"').strip("'")
                # Handle arrays like tags: ["a", "b"]
                if value.startswith('['):
                    value = re.findall(r'"([^"]+)"', value)
                front_matter[key] = value

        # Remove front matter from content
        content = content[match.end():]

    return front_matter, content


def convert_image_urls(content, github_user, repo, branch="main"):
    """Convert relative image paths to raw GitHub URLs."""
    # Pattern for local images: ![alt](../static/images/foo.jpg) or ![alt](/images/foo.jpg)
    def replace_local_image(match):
        alt = match.group(1)
        path = match.group(2)

        # Skip if already a full URL
        if path.startswith('http'):
            return match.group(0)

        # Clean up the path
        path = path.lstrip('./')
        if path.startswith('static/'):
            path = path[7:]  # Remove 'static/' prefix
        if not path.startswith('images/'):
            path = 'images/' + path.lstrip('/')

        github_url = f"https://raw.githubusercontent.com/{github_user}/{repo}/{branch}/static/{path}"
        return f"![{alt}]({github_url})"

    content = re.sub(r'!\[([^\]]*)\]\(([^)]+)\)', replace_local_image, content)
    return content


def publish_to_medium(markdown_path, publish_status="draft", canonical_url=None):
    """Publish a markdown file to Medium."""
    token, user_id = get_medium_credentials()

    # Read markdown file
    path = Path(markdown_path)
    if not path.exists():
        print(f"Error: File not found: {markdown_path}")
        sys.exit(1)

    content = path.read_text()

    # Parse front matter
    front_matter, content = parse_front_matter(content)

    # Get title from front matter or first H1
    title = front_matter.get('title')
    if not title:
        h1_match = re.search(r'^#\s+(.+)$', content, re.MULTILINE)
        title = h1_match.group(1) if h1_match else path.stem.replace('-', ' ').title()

    # Convert image URLs (adjust github_user and repo as needed)
    content = convert_image_urls(content, "kvsankar", "blog")

    # Get tags from front matter
    tags = front_matter.get('tags', [])
    if isinstance(tags, str):
        tags = [tags]
    tags = tags[:5]  # Medium allows max 5 tags

    # Prepare payload
    payload = {
        "title": title,
        "contentFormat": "markdown",
        "content": content,
        "publishStatus": publish_status,
        "tags": tags,
    }

    if canonical_url:
        payload["canonicalUrl"] = canonical_url

    # Publish
    print(f"Publishing '{title}' to Medium as {publish_status}...")
    response = requests.post(
        f"https://api.medium.com/v1/users/{user_id}/posts",
        headers={
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
        },
        json=payload
    )

    if response.status_code == 201:
        data = response.json()["data"]
        print(f"Success! Post published as {publish_status}")
        print(f"URL: {data['url']}")
        return data
    else:
        print(f"Error: {response.status_code}")
        print(response.text)
        sys.exit(1)


def main():
    parser = argparse.ArgumentParser(
        description="Cross-post Hugo markdown files to Medium"
    )
    parser.add_argument("file", help="Path to markdown file")
    parser.add_argument(
        "--publish",
        action="store_true",
        help="Publish immediately (default is draft)"
    )
    parser.add_argument(
        "--canonical",
        help="Canonical URL (your blog post URL for SEO)"
    )

    args = parser.parse_args()

    status = "public" if args.publish else "draft"
    publish_to_medium(args.file, publish_status=status, canonical_url=args.canonical)


if __name__ == "__main__":
    main()
