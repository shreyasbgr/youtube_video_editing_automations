import srt

def count_words_kannada(text):
    """Counts words in a Kannada subtitle line."""
    return len(text.strip().split())

def merge_subtitles(file_path, lines_per_group=2, min_words=2):
    with open(file_path, 'r', encoding='utf-8') as f:
        subs = list(srt.parse(f.read()))

    merged_subs = []
    i = 0
    while i < len(subs):
        merged_text = subs[i].content.strip()
        start_time = subs[i].start
        end_time = subs[i].end
        count = 1  # Tracks number of merged lines

        # Try merging lines_per_group OR small-word lines together
        while count < lines_per_group and i + count < len(subs):
            next_text = subs[i + count].content.strip()
            if count_words_kannada(next_text) <= min_words:  # Merge if 2 or fewer words
                merged_text += " " + next_text  # Use space for better readability
            else:
                merged_text += "\n" + next_text  # Normal merge for multi-line
            end_time = subs[i + count].end
            count += 1

        merged_subs.append(srt.Subtitle(index=len(merged_subs) + 1, start=start_time, end=end_time, content=merged_text))
        i += count  # Move to the next unprocessed subtitle

    new_srt = srt.compose(merged_subs)

    with open("merged_subtitles.srt", "w", encoding="utf-8") as f:
        f.write(new_srt)

# Usage: Merge lines with 2 or fewer words
merge_subtitles("ok.srt", lines_per_group=4, min_words=2)
