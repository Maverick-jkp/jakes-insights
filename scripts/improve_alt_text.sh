#!/bin/bash

# Script to improve image alt text across all blog posts
# Uses post title, filename, and context to generate descriptive alt text

CONTENT_DIR="/Users/jakepark/projects/jakes-tech-insights/content"
REPORT_FILE="/Users/jakepark/projects/jakes-tech-insights/alt_text_report.txt"
TEMP_LOG="/tmp/alt_text_changes.log"

# Initialize report and temp log
echo "Image Alt Text Improvement Report" > "$REPORT_FILE"
echo "Generated: $(date)" >> "$REPORT_FILE"
echo "========================================" >> "$REPORT_FILE"
echo "" >> "$REPORT_FILE"

> "$TEMP_LOG"

# Function to generate improved alt text based on context
generate_alt_text() {
    local file="$1"
    local image_filename="$2"
    local current_alt="$3"
    
    # Extract post title from frontmatter
    local title=$(grep "^title:" "$file" | head -1 | sed 's/^title: *"\(.*\)"$/\1/' | sed 's/^title: *\(.*\)$/\1/')
    
    # Extract category
    local category=$(grep "^categories:" "$file" | sed 's/.*"\(.*\)".*/\1/')
    
    # Clean up filename to get topic
    local topic=$(echo "$image_filename" | sed 's/^[0-9-]*//; s/\.jpg$//; s/\.png$//; s/-/ /g')
    
    # Generate improved alt text based on patterns
    local new_alt=""
    
    # Pattern matching for better alt text
    if [[ "$image_filename" =~ photography.*tips ]] || [[ "$topic" =~ photo.*tip ]]; then
        new_alt="Professional photography guide: essential camera techniques and composition tips"
    elif [[ "$category" == "entertainment" ]]; then
        if [[ "$topic" =~ (movie|film|cinema|映画|爆弾) ]]; then
            new_alt="Film review and analysis: $(echo "$topic" | sed 's/^ *//;s/ *$//' | cut -c1-60)"
        elif [[ "$topic" =~ (game|gaming|fortnite|ゲーム|独学) ]]; then
            new_alt="Gaming guide: $(echo "$topic" | sed 's/^ *//;s/ *$//' | cut -c1-70)"
        elif [[ "$topic" =~ (gundam|ガンダム|閃光|ハサウェイ) ]]; then
            new_alt="Anime analysis: Mobile Suit Gundam Hathaway's Flash story breakdown"
        elif [[ "$image_filename" =~ quinton.*aaron ]]; then
            new_alt="Actor profile: Quinton Aaron career highlights and achievements"
        else
            # Use title but make it more descriptive
            new_alt="Entertainment spotlight: $(echo "$title" | cut -c1-65)"
        fi
    elif [[ "$category" == "technology" ]]; then
        new_alt="Technology insights: $(echo "$title" | cut -c1-65)"
    elif [[ "$category" == "lifestyle" ]]; then
        new_alt="Lifestyle guide: $(echo "$title" | cut -c1-70)"
    elif [[ "$category" == "business" ]]; then
        new_alt="Business analysis: $(echo "$title" | cut -c1-65)"
    else
        # Generic fallback using title
        new_alt="Featured article: $(echo "$title" | cut -c1-75)"
    fi
    
    # Ensure alt text is between 50-100 characters
    local alt_length=${#new_alt}
    if [ $alt_length -gt 100 ]; then
        new_alt="${new_alt:0:97}..."
    elif [ $alt_length -lt 50 ]; then
        # Pad with category context if too short
        new_alt="$new_alt - in-depth coverage"
        new_alt="${new_alt:0:100}"
    fi
    
    echo "$new_alt"
}

# Function to process a single file
process_file() {
    local file="$1"
    local lang=$(echo "$file" | grep -oE '/(en|ko|ja)/' | tr -d '/')
    local changed=0
    
    # Check if file contains images
    if ! grep -q "!\[.*\](/images/" "$file"; then
        return
    fi
    
    # Process each image in the file
    while IFS= read -r image_line; do
        # Extract current alt text and filename
        current_alt=$(echo "$image_line" | sed -n 's/!\[\(.*\)\](\/images\/.*/\1/p')
        image_filename=$(echo "$image_line" | sed -n 's/!\[.*\](\/images\/\(.*\))/\1/p')
        
        # Skip if alt text is already descriptive (50-100 chars with context words)
        if [ ${#current_alt} -ge 50 ] && [ ${#current_alt} -le 100 ]; then
            echo "[SKIP] $file - Alt already good" >> "$REPORT_FILE"
            continue
        fi
        
        # Generate new alt text
        new_alt=$(generate_alt_text "$file" "$image_filename" "$current_alt")
        
        # Only proceed if new alt text is different and better
        if [ "$current_alt" = "$new_alt" ]; then
            continue
        fi
        
        # Create backup on first change
        if [ $changed -eq 0 ]; then
            cp "$file" "$file.bak"
        fi
        
        # Replace alt text in file
        # Use perl for more reliable replacement with special characters
        perl -i -pe "s/\Q![$current_alt](/images/$image_filename)\E/![$new_alt](\/images\/$image_filename)/" "$file"
        
        changed=1
        echo "CHANGE" >> "$TEMP_LOG"
        
        # Log the change
        echo "[$lang] $(basename "$file")" >> "$REPORT_FILE"
        echo "  Image: $image_filename" >> "$REPORT_FILE"
        echo "  Old: \"$current_alt\" (${#current_alt} chars)" >> "$REPORT_FILE"
        echo "  New: \"$new_alt\" (${#new_alt} chars)" >> "$REPORT_FILE"
        echo "" >> "$REPORT_FILE"
        
        echo "  ✓ Updated: $(basename "$file") - $image_filename"
        
    done < <(grep "!\[.*\](/images/" "$file")
}

# Main processing
echo ""
echo "========================================="
echo "Image Alt Text Improvement Tool"
echo "========================================="
echo "Scanning for images in $CONTENT_DIR..."
echo ""

# Count total images first
total_images=$(find "$CONTENT_DIR" -type f -name "*.md" ! -name "all-posts.md" -exec grep -h "!\[.*\](/images/" {} \; | wc -l | tr -d ' ')
echo "Found $total_images images to process"
echo ""

# Process all files
find "$CONTENT_DIR" -type f -name "*.md" ! -name "all-posts.md" | sort | while read -r file; do
    if grep -q "!\[.*\](/images/" "$file"; then
        process_file "$file"
    fi
done

# Count changes made
changes_made=$(wc -l < "$TEMP_LOG" | tr -d ' ')

# Generate summary
echo "" >> "$REPORT_FILE"
echo "========================================" >> "$REPORT_FILE"
echo "SUMMARY" >> "$REPORT_FILE"
echo "========================================" >> "$REPORT_FILE"
echo "Total images found: $total_images" >> "$REPORT_FILE"
echo "Alt text improvements: $changes_made" >> "$REPORT_FILE"
echo "Completion time: $(date)" >> "$REPORT_FILE"

# Clean up
rm -f "$TEMP_LOG"

echo ""
echo "========================================="
echo "Alt Text Improvement Complete"
echo "========================================="
echo "Total images found: $total_images"
echo "Changes made: $changes_made"
echo ""
echo "Report saved to: $REPORT_FILE"
echo "Backup files created with .bak extension"
echo ""
echo "Review changes with: git diff"
echo "========================================="

