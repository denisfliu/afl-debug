#!/bin/bash

# Input file
input_file="/tmp/time.txt"

# Output directory
output_dir="time/"

# Create output directory if it doesn't exist
mkdir -p "$output_dir"
rm -r -f time/*

# Counter for output files
file_counter=1

# Loop through the input file
while IFS= read -r line; do
    if [[ $line == "Index: 0"* ]]; then
        # Start a new output file
	touch "$output_dir/output_$file_counter.txt"
        output_file="$output_dir/output_$file_counter.txt"
        ((file_counter++))
        echo "$line" >> "$output_file"
    else
        # Append line to the current output file
        echo "$line" >> "$output_file"
    fi
done < "$input_file"
