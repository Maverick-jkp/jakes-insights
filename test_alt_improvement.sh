#!/bin/bash

TEST_FILE="content/en/entertainment/2026-02-03-photography-tips.md"

# Extract components
title=$(grep "^title:" "$TEST_FILE" | head -1 | sed 's/^title: *"\(.*\)"$/\1/')
category=$(grep "^categories:" "$TEST_FILE" | sed 's/.*"\(.*\)".*/\1/')
image_line=$(grep "!\[.*\](/images/" "$TEST_FILE")
current_alt=$(echo "$image_line" | sed -n 's/!\[\(.*\)\](\/images\/.*/\1/p')
image_filename=$(echo "$image_line" | sed -n 's/!\[.*\](\/images\/\(.*\))/\1/p')

echo "File: $TEST_FILE"
echo "Title: $title"
echo "Category: $category"
echo "Image line: $image_line"
echo "Current alt: $current_alt (${#current_alt} chars)"
echo "Image filename: $image_filename"
echo ""
echo "New alt text would be:"
echo "Professional photography guide: essential camera techniques and composition tips"

