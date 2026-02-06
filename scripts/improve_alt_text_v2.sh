#!/bin/bash

# Script to improve image alt text across all blog posts
# Version 2: Uses awk for more reliable text replacement

CONTENT_DIR="/Users/jakepark/projects/jakes-tech-insights/content"
REPORT_FILE="/Users/jakepark/projects/jakes-tech-insights/alt_text_report.txt"
TEMP_LOG="/tmp/alt_text_changes.log"

# Initialize report
echo "Image Alt Text Improvement Report" > "$REPORT_FILE"
echo "Generated: $(date)" >> "$REPORT_FILE"
echo "========================================" >> "$REPORT_FILE"
echo "" >> "$REPORT_FILE"

> "$TEMP_LOG"

# Function to generate improved alt text
generate_alt_text() {
    local file="$1"
    local image_filename="$2"
    local current_alt="$3"
    
    # Extract post title
    local title=$(grep "^title:" "$file" | head -1 | sed 's/^title: *"\(.*\)"$/\1/' | sed 's/^title: *\(.*\)$/\1/' | sed 's/"$//')
    
    # Extract category
    local category=$(grep "^categories:" "$file" | sed 's/.*"\([^"]*\)".*/\1/')
    
    # Clean filename to get topic
    local topic=$(echo "$image_filename" | sed 's/^[0-9-]*//; s/\.jpg$//; s/\.png$//; s/-/ /g')
    
    local new_alt=""
    
    # Smart pattern matching for alt text generation
    if [[ "$image_filename" =~ photography.*tips ]] || [[ "$topic" =~ photo.*tip ]]; then
        new_alt="Professional photography guide: essential camera techniques and composition tips"
    elif [[ "$image_filename" =~ quinton.*aaron ]]; then
        new_alt="Actor profile: Quinton Aaron career highlights and achievements"
    elif [[ "$topic" =~ (gundam|ガンダム|閃光|ハサウェイ|キルケー) ]]; then
        new_alt="Anime analysis: Mobile Suit Gundam Hathaway's Flash story breakdown"
    elif [[ "$topic" =~ (movie|film|cinema|映画|爆弾) ]]; then
        new_alt="Film review: $(echo "$title" | cut -c1-70)"
    elif [[ "$topic" =~ (game|gaming|fortnite|ゲーム) ]]; then
        new_alt="Gaming guide: $(echo "$title" | cut -c1-70)"
    elif [[ "$category" == "entertainment" ]]; then
        new_alt="Entertainment spotlight: $(echo "$title" | cut -c1-60)"
    elif [[ "$category" == "technology" ]]; then
        new_alt="Technology insights: $(echo "$title" | cut -c1-65)"
    elif [[ "$category" == "lifestyle" ]]; then
        new_alt="Lifestyle guide: $(echo "$title" | cut -c1-70)"
    elif [[ "$category" == "business" ]]; then
        new_alt="Business analysis: $(echo "$title" | cut -c1-65)"
    else
        new_alt="Featured article: $(echo "$title" | cut -c1-70)"
    fi
    
    # Ensure 50-100 character range
    local alt_length=${#new_alt}
    if [ $alt_length -gt 100 ]; then
        new_alt="${new_alt:0:97}..."
    elif [ $alt_length -lt 50 ]; then
        new_alt="$new_alt - in-depth coverage"
        new_alt="${new_alt:0:100}"
    fi
    
    echo "$new_alt"
}

# Function to process a file
process_file() {
    local file="$1"
    local basename=$(basename "$file")
    local lang=$(echo "$file" | grep -oE '/(en|ko|ja)/' | tr -d '/')
    
    # Skip if no images
    if ! grep -q "!\[.*\](/images/" "$file"; then
        return
    fi
    
    # Create backup
    cp "$file" "$file.bak"
    
    # Process file with awk
    awk -v reportfile="$REPORT_FILE" -v templog="$TEMP_LOG" -v filepath="$file" -v lang="$lang" -v bname="$basename" '
    BEGIN {
        # Read title and category from file
        while ((getline line < filepath) > 0) {
            if (line ~ /^title:/) {
                gsub(/^title: *"?/, "", line)
                gsub(/"$/, "", line)
                title = line
            }
            if (line ~ /^categories:/) {
                match(line, /"([^"]*)"/, arr)
                category = arr[1]
            }
            if (line ~ /^---$/ && NR > 1) break
        }
        close(filepath)
    }
    
    /^!\[.*\]\(\/images\// {
        # Extract current alt and filename
        match($0, /!\[([^\]]*)\]\(\/images\/([^\)]*)\)/, arr)
        current_alt = arr[1]
        img_filename = arr[2]
        
        # Only process if alt text is short (< 50 chars)
        if (length(current_alt) < 50) {
            # Generate new alt text based on filename patterns
            new_alt = ""
            topic = img_filename
            gsub(/^[0-9-]*/, "", topic)
            gsub(/\.jpg$/, "", topic)
            gsub(/\.png$/, "", topic)
            gsub(/-/, " ", topic)
            
            # Pattern matching
            if (img_filename ~ /photography.*tips/ || topic ~ /photo.*tip/) {
                new_alt = "Professional photography guide: essential camera techniques and composition tips"
            } else if (img_filename ~ /quinton.*aaron/) {
                new_alt = "Actor profile: Quinton Aaron career highlights and achievements"
            } else if (topic ~ /(gundam|ガンダム|閃光|ハサウェイ|キルケー)/) {
                new_alt = "Anime analysis: Mobile Suit Gundam Hathaway Flash story breakdown"
            } else if (topic ~ /(movie|film|cinema|映画|爆弾)/) {
                new_alt = "Film review: " substr(title, 1, 70)
            } else if (topic ~ /(game|gaming|fortnite|ゲーム)/) {
                new_alt = "Gaming guide: " substr(title, 1, 70)
            } else if (category == "entertainment") {
                new_alt = "Entertainment spotlight: " substr(title, 1, 60)
            } else if (category == "technology") {
                new_alt = "Technology insights: " substr(title, 1, 65)
            } else if (category == "lifestyle") {
                new_alt = "Lifestyle guide: " substr(title, 1, 70)
            } else if (category == "business") {
                new_alt = "Business analysis: " substr(title, 1, 65)
            } else {
                new_alt = "Featured article: " substr(title, 1, 70)
            }
            
            # Ensure length constraints
            if (length(new_alt) > 100) {
                new_alt = substr(new_alt, 1, 97) "..."
            } else if (length(new_alt) < 50) {
                new_alt = new_alt " - in-depth coverage"
                if (length(new_alt) > 100) {
                    new_alt = substr(new_alt, 1, 100)
                }
            }
            
            # Log the change
            print "[" lang "] " bname >> reportfile
            print "  Image: " img_filename >> reportfile
            print "  Old: \"" current_alt "\" (" length(current_alt) " chars)" >> reportfile
            print "  New: \"" new_alt "\" (" length(new_alt) " chars)" >> reportfile
            print "" >> reportfile
            
            print "CHANGE" >> templog
            
            # Replace the line
            gsub(/!\[.*\]\(\/images\/.*\)/, "![" new_alt "](/images/" img_filename ")")
        }
    }
    
    { print }
    ' "$file" > "$file.tmp"
    
    # Replace original with modified version
    mv "$file.tmp" "$file"
}

# Main execution
echo ""
echo "========================================="
echo "Image Alt Text Improvement Tool v2"
echo "========================================="
echo "Scanning for images in $CONTENT_DIR..."
echo ""

# Count total images
total_images=$(find "$CONTENT_DIR" -type f -name "*.md" ! -name "all-posts.md" -exec grep -h "!\[.*\](/images/" {} \; | wc -l | tr -d ' ')
echo "Found $total_images images to process"
echo ""

# Process all files
find "$CONTENT_DIR" -type f -name "*.md" ! -name "all-posts.md" | sort | while read -r file; do
    if grep -q "!\[.*\](/images/" "$file"; then
        echo "  Processing: $(basename "$file")"
        process_file "$file"
    fi
done

# Count changes
changes_made=$(wc -l < "$TEMP_LOG" 2>/dev/null | tr -d ' ')
if [ -z "$changes_made" ]; then
    changes_made=0
fi

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
echo "Report: $REPORT_FILE"
echo "Backup files: *.bak"
echo ""
echo "Review changes: git diff"
echo "========================================="

