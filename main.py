import os
import subprocess
import requests
import srt
from bs4 import BeautifulSoup
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials

# Constants
SCOPES = [
    "https://www.googleapis.com/auth/youtube.upload",
    "https://www.googleapis.com/auth/youtube.force-ssl",
    "https://www.googleapis.com/auth/youtubepartner",
    "https://www.googleapis.com/auth/youtube.readonly"
]
CLIENT_SECRETS_FILE = "client_secrets.json"
TOKEN_FILE = "token.json"

# Function to authenticate YouTube API
def authenticate_youtube():
    creds = None
    if os.path.exists(TOKEN_FILE):
        creds = Credentials.from_authorized_user_file(TOKEN_FILE, SCOPES)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(CLIENT_SECRETS_FILE, SCOPES)
            creds = flow.run_local_server(port=0)
        with open(TOKEN_FILE, "w") as token:
            token.write(creds.to_json())
    return build("youtube", "v3", credentials=creds)

# Function to create a video with FFmpeg
def create_video(image, audio, output_video):
    command = [
        "ffmpeg", "-loop", "1", "-i", image,
        "-i", audio, "-c:v", "libx264", "-tune", "stillimage",
        "-preset", "ultrafast", "-c:a", "aac", "-b:a", "128k",
        "-shortest", "-movflags", "+faststart", output_video
    ]
    subprocess.run(command)

# Function to upload video to YouTube
def upload_video(youtube, file_path, title):
    request = youtube.videos().insert(
        part="snippet,status",
        body={
            "snippet": {"title": title, "description": "Auto-uploaded video", "tags": ["test", "upload"]},
            "status": {"privacyStatus": "unlisted"}
        },
        media_body=MediaFileUpload(file_path, chunksize=-1, resumable=True)
    )
    response = request.execute()
    return response["id"]

# Function to download captions from DownSub
def download_captions_downsub(video_id):
    downsub_url = f"https://downsub.com/?url=https://www.youtube.com/watch?v={video_id}"
    print(f"Fetching captions from: {downsub_url}")
    response = requests.get(downsub_url)
    if response.status_code == 200:
        soup = BeautifulSoup(response.text, 'html.parser')
        download_link = soup.find("a", class_="btn btn-primary btn-lg")
        if download_link:
            captions_url = download_link["href"]
            captions_response = requests.get(captions_url)
            if captions_response.status_code == 200:
                with open(f"{video_id}.srt", "wb") as file:
                    file.write(captions_response.content)
                print(f"Captions downloaded successfully as {video_id}.srt")
            else:
                print("Failed to download captions.")
        else:
            print("Download link not found on DownSub.")
    else:
        print("Failed to fetch DownSub page.")

# Function to count words in Kannada
def count_words_kannada(text):
    return len(text.strip().split())

# Function to merge subtitles with user input
def merge_subtitles():
    file_path = input("Enter subtitle file path (.srt): ")
    lines_per_group = int(input("Enter number of lines to merge per group: "))
    min_words = int(input("Enter minimum words per line before merging: "))
    
    with open(file_path, 'r', encoding='utf-8') as f:
        subs = list(srt.parse(f.read()))
    
    merged_subs = []
    i = 0
    while i < len(subs):
        merged_text = subs[i].content.strip()
        start_time = subs[i].start
        end_time = subs[i].end
        count = 1  # Tracks number of merged lines
        
        while count < lines_per_group and i + count < len(subs):
            next_text = subs[i + count].content.strip()
            if count_words_kannada(next_text) <= min_words:
                merged_text += " " + next_text
            else:
                merged_text += "\n" + next_text
            end_time = subs[i + count].end
            count += 1
        
        merged_subs.append(srt.Subtitle(index=len(merged_subs) + 1, start=start_time, end=end_time, content=merged_text))
        i += count
    
    new_srt = srt.compose(merged_subs)
    with open("merged_subtitles.srt", "w", encoding="utf-8") as f:
        f.write(new_srt)
    print("Merged subtitles saved as merged_subtitles.srt")

# Main execution
def main():
    youtube = authenticate_youtube()
    
    print("Select one or multiple steps (e.g., 1,4,5):")
    print("1 - Merge Subtitles")
    print("2 - Generate Video Only")
    print("3 - Generate and Upload Video")
    print("4 - Upload Existing Video")
    print("5 - Download Captions via DownSub")
    
    choices = input("Enter choices: ").split(',')
    
    if "1" in choices:
        merge_subtitles()
    if "2" in choices:
        create_video("background.png", "audio.m4a", "output.mp4")
    if "3" in choices:
        create_video("background.png", "audio.m4a", "output.mp4")
        video_id = upload_video(youtube, "output.mp4", "Auto-uploaded Video")
        print(f"Video Uploaded: https://www.youtube.com/watch?v={video_id}")
    if "4" in choices:
        existing_file = input("Enter video file path: ")
        video_id = upload_video(youtube, existing_file, "Auto-uploaded Video")
        print(f"Video Uploaded: https://www.youtube.com/watch?v={video_id}")
    if "5" in choices:
        video_id = input("Enter YouTube Video ID: ")
        download_captions_downsub(video_id)

if __name__ == "__main__":
    main()
