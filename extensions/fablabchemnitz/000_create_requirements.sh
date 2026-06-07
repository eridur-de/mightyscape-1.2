#!/bin/bash

# Find all unique directories containing .py files
find . -type f -name "*.py" -exec dirname {} \; | sort -u | while read -r dir; do
    echo "Generating requirements.txt for: $dir"

    # 1. Run pipreqs using uv with --mode no-pin
    uv run --with pipreqs pipreqs "$dir" --force --mode no-pin 2> >(grep -Ev "Not scanning for jupyter notebooks|Successfully saved requirements file" >&2)

    # 2. Check if the file was created, then remove 'inkex' if it exists
    if [ -f "$dir/requirements.txt" ]; then
        # Creates a temp file without inkex, then overwrites the original
        grep -vEi '^inkex(==|~=|>=|$)' "$dir/requirements.txt" > "$dir/requirements.tmp" && mv "$dir/requirements.tmp" "$dir/requirements.txt"
    fi
done
