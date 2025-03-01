import yt_dlp
import argparse
import os
import json
import requests

def get_subtitles(video_id, lang):
    url = f"https://www.youtube.com/watch?v={video_id}"
    ydl_opts = {
        "skip_download": True,
        "writesubtitles": True,
        "writeautomaticsub": True,
        "subtitleslangs": [lang],
        "quiet": True,
    }
    
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=False)
        auto_subtitles = info.get("automatic_captions", {})
        
        if lang in auto_subtitles:
            print(f"Using auto-generated captions for {lang}.")
            return auto_subtitles[lang]
        else:
            print("No subtitles found.")
            return None

def download_and_parse_json(subtitles):
    if not subtitles:
        print("No subtitles to process.")
        return None
    
    json_url = subtitles[0]['url']
    response = requests.get(json_url)
    if response.status_code == 200:
        return response.json()
    else:
        print("Failed to download subtitles JSON.")
        return None

def convert_to_srt(subtitle_data, output_filename):
    if not subtitle_data or "events" not in subtitle_data:
        print("Invalid subtitle data.")
        return
    
    srt_output = ""
    index = 1
    for event in subtitle_data["events"]:
        if "segs" in event:
            start_time = event["tStartMs"]
            
            for i, seg in enumerate(event["segs"]):
                if "utf8" in seg:
                    word = seg["utf8"]
                    word_start = start_time + seg.get("tOffsetMs", 0)
                    
                    # Determine end time properly
                    if i + 1 < len(event["segs"]):
                        word_end = start_time + event["segs"][i + 1].get("tOffsetMs", 0)
                    else:
                        # Look at the next event's start time
                        next_event = next((e for e in subtitle_data["events"] if e["tStartMs"] > word_start), None)
                        if next_event:
                            word_end = next_event["tStartMs"]
                        else:
                            word_end = word_start + 500  # Default duration fallback
                    
                    # Convert time format to SRT (hh:mm:ss,ms)
                    start_srt = ms_to_srt(word_start)
                    end_srt = ms_to_srt(word_end)
                    
                    srt_output += f"{index}\n{start_srt} --> {end_srt}\n{word}\n\n"
                    index += 1
    
    with open(output_filename, "w", encoding="utf-8") as f:
        f.write(srt_output)
    print(f"Subtitles saved as {output_filename}")

def ms_to_srt(ms):
    hours = ms // 3600000
    minutes = (ms % 3600000) // 60000
    seconds = (ms % 60000) // 1000
    milliseconds = ms % 1000
    return f"{hours:02}:{minutes:02}:{seconds:02},{milliseconds:03}"

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("video_id", help="YouTube video ID")
    parser.add_argument("--lang", default="en", help="Subtitle language (default: English)")
    args = parser.parse_args()
    
    subtitles = get_subtitles(args.video_id, args.lang)
    subtitle_data = download_and_parse_json(subtitles)
    if subtitle_data:
        output_filename = f"{args.video_id}_{args.lang}.srt"
        convert_to_srt(subtitle_data, output_filename)

if __name__ == "__main__":
    main()
