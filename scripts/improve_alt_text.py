#!/usr/bin/env python3
"""
Script to improve image alt text across all blog posts
Uses post context to generate descriptive, SEO-friendly alt text (50-100 chars)
"""

import os
import re
from pathlib import Path
from datetime import datetime

CONTENT_DIR = Path("/Users/jakepark/projects/jakes-tech-insights/content")
REPORT_FILE = Path("/Users/jakepark/projects/jakes-tech-insights/alt_text_report.txt")

def extract_frontmatter(content):
    """Extract title and category from frontmatter"""
    title_match = re.search(r'^title:\s*["\']?([^"\n]+)["\']?', content, re.MULTILINE)
    category_match = re.search(r'categories:\s*\["([^"]+)"\]', content)
    
    title = title_match.group(1).strip('"') if title_match else ""
    category = category_match.group(1) if category_match else ""
    
    return title, category

def generate_alt_text(title, category, image_filename, current_alt):
    """Generate improved alt text based on context"""
    
    # Extract topic from filename
    topic = re.sub(r'^\d{8}-', '', image_filename)
    topic = re.sub(r'\.(jpg|png)$', '', topic)
    topic = topic.replace('-', ' ')
    
    # Pattern-based alt text generation
    if 'photography' in image_filename and 'tips' in image_filename:
        new_alt = "Professional photography guide: essential camera techniques and composition tips"
    elif 'quinton' in image_filename and 'aaron' in image_filename:
        new_alt = "Actor profile: Quinton Aaron career highlights and achievements"
    elif any(word in topic for word in ['gundam']):
        new_alt = "Anime analysis: Mobile Suit Gundam Hathaway Flash story breakdown"
    elif any(word in topic for word in ['movie', 'film', 'cinema']):
        new_alt = f"Film review: {title[:70]}"
    elif any(word in topic for word in ['game', 'gaming', 'fortnite']):
        new_alt = f"Gaming guide: {title[:70]}"
    elif category == 'entertainment':
        new_alt = f"Entertainment spotlight: {title[:60]}"
    elif category == 'technology':
        new_alt = f"Technology insights: {title[:65]}"
    elif category == 'lifestyle':
        new_alt = f"Lifestyle guide: {title[:70]}"
    elif category == 'business':
        new_alt = f"Business analysis: {title[:65]}"
    else:
        new_alt = f"Featured article: {title[:70]}"
    
    # Ensure 50-100 character range
    if len(new_alt) > 100:
        new_alt = new_alt[:97] + "..."
    elif len(new_alt) < 50:
        new_alt = new_alt + " - in-depth coverage"
        if len(new_alt) > 100:
            new_alt = new_alt[:100]
    
    return new_alt

def process_file(filepath):
    """Process a single markdown file"""
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Find all image markdown
    image_pattern = r'!\[([^\]]*)\]\(/images/([^\)]+)\)'
    matches = list(re.finditer(image_pattern, content))
    
    if not matches:
        return []
    
    # Extract metadata
    title, category = extract_frontmatter(content)
    lang = 'en' if '/en/' in str(filepath) else 'ko'
    
    changes = []
    new_content = content
    
    for match in matches:
        current_alt = match.group(1)
        image_filename = match.group(2)
        
        # Only process if alt text is short (< 50 chars)
        if len(current_alt) >= 50:
            continue
        
        # Generate new alt text
        new_alt = generate_alt_text(title, category, image_filename, current_alt)
        
        # Replace in content
        old_markdown = f'![{current_alt}](/images/{image_filename})'
        new_markdown = f'![{new_alt}](/images/{image_filename})'
        new_content = new_content.replace(old_markdown, new_markdown)
        
        changes.append({
            'file': filepath.name,
            'lang': lang,
            'image': image_filename,
            'old_alt': current_alt,
            'new_alt': new_alt,
            'old_len': len(current_alt),
            'new_len': len(new_alt)
        })
    
    if changes:
        # Create backup
        backup_path = filepath.with_suffix('.md.bak')
        with open(backup_path, 'w', encoding='utf-8') as f:
            f.write(content)
        
        # Write updated content
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(new_content)
    
    return changes

def main():
    print()
    print("=" * 60)
    print("Image Alt Text Improvement Tool (Python)")
    print("=" * 60)
    print(f"Scanning: {CONTENT_DIR}")
    print()
    
    # Find all markdown files with images
    md_files = []
    for md_file in CONTENT_DIR.rglob("*.md"):
        if md_file.name == "all-posts.md":
            continue
        with open(md_file, 'r', encoding='utf-8') as f:
            if '](/images/' in f.read():
                md_files.append(md_file)
    
    total_images = sum(1 for f in md_files for _ in re.finditer(r'!\[.*?\]\(/images/', f.read_text()))
    print(f"Found {len(md_files)} files with {total_images} images")
    print()
    
    # Process all files
    all_changes = []
    for filepath in sorted(md_files):
        changes = process_file(filepath)
        if changes:
            print(f"  ✓ Updated: {filepath.name} ({len(changes)} images)")
            all_changes.extend(changes)
    
    # Generate report
    with open(REPORT_FILE, 'w', encoding='utf-8') as report:
        report.write("Image Alt Text Improvement Report\n")
        report.write(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        report.write("=" * 60 + "\n\n")
        
        for change in all_changes:
            report.write(f"[{change['lang']}] {change['file']}\n")
            report.write(f"  Image: {change['image']}\n")
            report.write(f"  Old: \"{change['old_alt']}\" ({change['old_len']} chars)\n")
            report.write(f"  New: \"{change['new_alt']}\" ({change['new_len']} chars)\n")
            report.write("\n")
        
        report.write("\n" + "=" * 60 + "\n")
        report.write("SUMMARY\n")
        report.write("=" * 60 + "\n")
        report.write(f"Total images found: {total_images}\n")
        report.write(f"Alt text improvements: {len(all_changes)}\n")
        report.write(f"Completion time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
    
    print()
    print("=" * 60)
    print("Alt Text Improvement Complete")
    print("=" * 60)
    print(f"Total images found: {total_images}")
    print(f"Changes made: {len(all_changes)}")
    print()
    print(f"Report: {REPORT_FILE}")
    print("Backup files: *.md.bak")
    print()
    print("Review changes: git diff")
    print("=" * 60)

if __name__ == "__main__":
    main()
