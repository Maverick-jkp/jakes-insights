#!/bin/bash
#
# Category Migration Script: 8 → 5 Categories
# Date: 2026-01-25
#
# Migration mapping:
# - education → tech
# - finance → business
# - lifestyle → society
#

set -e

echo "========================================="
echo "  Category Migration: 8 → 5"
echo "========================================="
echo ""

# Count posts before migration
echo "📊 Current post distribution:"
for lang in en ko ja; do
    for cat in tech business lifestyle society entertainment sports finance education; do
        count=$(find content/$lang/$cat -name "*.md" 2>/dev/null | wc -l | tr -d ' ')
        if [ "$count" -gt 0 ]; then
            echo "  content/$lang/$cat: $count posts"
        fi
    done
done
echo ""

echo "🔄 Starting migration..."
echo ""

# Function to migrate posts and update frontmatter
migrate_category() {
    local lang=$1
    local old_cat=$2
    local new_cat=$3

    local old_dir="content/$lang/$old_cat"
    local new_dir="content/$lang/$new_cat"

    if [ ! -d "$old_dir" ]; then
        echo "  ⏭️  Skipping $old_dir (doesn't exist)"
        return
    fi

    local count=$(find "$old_dir" -name "*.md" 2>/dev/null | wc -l | tr -d ' ')
    if [ "$count" -eq 0 ]; then
        echo "  ⏭️  Skipping $old_dir (empty)"
        rmdir "$old_dir" 2>/dev/null || true
        return
    fi

    echo "  📦 Migrating $old_dir → $new_dir ($count posts)"

    # Create target directory if it doesn't exist
    mkdir -p "$new_dir"

    # Move all markdown files
    find "$old_dir" -name "*.md" -type f | while read file; do
        filename=$(basename "$file")

        # Move file
        mv "$file" "$new_dir/$filename"

        # Update frontmatter category
        sed -i '' "s/categories: \[\"$old_cat\"\]/categories: [\"$new_cat\"]/" "$new_dir/$filename"
    done

    # Remove old directory
    rmdir "$old_dir" 2>/dev/null || true

    echo "     ✅ Migrated $count posts"
}

# Migrate for each language
for lang in en ko ja; do
    echo "🌍 Language: $lang"
    migrate_category "$lang" "education" "tech"
    migrate_category "$lang" "finance" "business"
    migrate_category "$lang" "lifestyle" "society"
    echo ""
done

echo "========================================="
echo "  ✅ Migration Complete!"
echo "========================================="
echo ""

# Count posts after migration
echo "📊 New post distribution:"
for lang in en ko ja; do
    for cat in tech business society entertainment sports; do
        count=$(find content/$lang/$cat -name "*.md" 2>/dev/null | wc -l | tr -d ' ')
        if [ "$count" -gt 0 ]; then
            echo "  content/$lang/$cat: $count posts"
        fi
    done
done
echo ""

echo "💡 Next steps:"
echo "   1. Review migrated posts: git diff content/"
echo "   2. Test Hugo build: /opt/homebrew/bin/hugo"
echo "   3. Commit changes: git add -A && git commit"
