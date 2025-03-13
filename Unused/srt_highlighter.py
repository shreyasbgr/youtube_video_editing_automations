import yt_dlp
import argparse
import os
import json
import requests
import re
import unicodedata
import difflib
from pysubparser import parser

def normalize_text(text):
    return unicodedata.normalize("NFKC", text.strip())

def time_to_ms(time_str):
    parts = re.split('[:,]', time_str)
    if len(parts) == 4:
        h, m, s, ms = map(int, parts)
    elif len(parts) == 3:
        h, m = map(int, parts[:2])
        s_ms = parts[2].split('.')
        s = int(s_ms[0])
        ms = int(s_ms[1]) if len(s_ms) > 1 else 0
    else:
        raise ValueError(f"Unexpected time format: {time_str}")
    return (h * 3600 + m * 60 + s) * 1000 + ms

def ms_to_ass(ms):
    hours = ms // 3600000
    minutes = (ms % 3600000) // 60000
    seconds = (ms % 60000) // 1000
    milliseconds = ms % 1000
    return f"{hours:01}:{minutes:02}:{seconds:02}.{milliseconds:02}"

def find_best_match(word, word_list):
    matches = difflib.get_close_matches(word, word_list, n=1, cutoff=0.5)
    return matches[0] if matches else None

def merge_subtitles(audiobook_file, word_level_file, output_file):
    audiobook_subs = list(parser.parse(audiobook_file))
    word_level_subs = list(parser.parse(word_level_file))
    
    output_json = []
    
    for base in audiobook_subs:
        base_start = time_to_ms(str(base.start))
        base_end = time_to_ms(str(base.end))
        base_text = normalize_text(base.text)
        base_words = base_text.split()
        words_to_highlight = []
        
        for word in word_level_subs:
            word_text = normalize_text(word.text)
            word_start = time_to_ms(str(word.start))
            word_end = time_to_ms(str(word.end))
            
            if base_start <= word_start <= base_end:
                words_to_highlight.append((word_text, word_start, word_end))
        
        word_list = [normalize_text(w) for w in base_words]
        
        for word, start, end in words_to_highlight:
            best_match = find_best_match(word, word_list)
            if best_match:
                highlighted_text = " ".join(["<mark>" + w + "</mark>" if normalize_text(w) == best_match else w for w in base_words])
                output_json.append({
                    "start": start,
                    "end": end,
                    "text": highlighted_text
                })
            else:
                output_json.append({
                    "start": base_start,
                    "end": base_end,
                    "text": base_text
                })
    
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(output_json, f, ensure_ascii=False, indent=4)
    print(f"Merged subtitles saved as {output_file}")

def main():
    parser_arg = argparse.ArgumentParser()
    parser_arg.add_argument("audiobook_srt", help="Audiobook SRT file with 3-line subtitles")
    parser_arg.add_argument("word_srt", help="Word-level SRT file")
    parser_arg.add_argument("output_json", help="Output merged JSON file")
    args = parser_arg.parse_args()
    
    merge_subtitles(args.audiobook_srt, args.word_srt, args.output_json)

if __name__ == "__main__":
    main()

# Usage:
# Run the script using the following command:
# python srt_highlighter.py audiobook_3lines.srt word_level.srt merged_highlighted.json
