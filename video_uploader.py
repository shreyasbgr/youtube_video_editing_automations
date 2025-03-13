"""
Usage:
This script automates the process of:
1. Generating a video from an image and audio using FFmpeg.
2. Uploading the generated video to YouTube.
3. Downloading the captions using DownSub directly.

Options:
1 - Generate Video Only
2 - Generate and Upload Video
3 - Upload Existing Video
4 - Download Captions via DownSub
5 - Upload Video and Download Captions
6 - Perform All Steps (Generate, Upload, Download Captions)

Requirements:
- Install `google-auth`, `google-auth-oauthlib`, `google-auth-httplib2`, and `google-api-python-client`
- `ffmpeg` must be installed and accessible in PATH.
- Create a `client_secrets.json` file for YouTube API authentication.
- Authenticate YouTube API before running the script.
- Captions are downloaded via DownSub directly.

Run the script and select an option based on the required task.
"""

import os
import subprocess
import requests
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

# Main execution
def main():
    youtube = authenticate_youtube()
    image = "background.png"
    audio = "audio.m4a"
    output_video = "output.mp4"
    title = "Auto-uploaded Video"
    
    print("Select mode:")
    print("1 - Generate Video Only")
    print("2 - Generate and Upload Video")
    print("3 - Upload Existing Video")
    print("4 - Download Captions via DownSub")
    print("5 - Upload Video and Download Captions")
    print("6 - Perform All Steps (Generate, Upload, Download Captions)")
    choice = input("Enter choice: ")
    
    if choice == "1":
        create_video(image, audio, output_video)
        print("Video Created Successfully")
    elif choice == "2":
        create_video(image, audio, output_video)
        video_id = upload_video(youtube, output_video, title)
        print(f"Video Uploaded: https://www.youtube.com/watch?v={video_id}")
    elif choice == "3":
        existing_file = input("Enter video file path: ")
        video_id = upload_video(youtube, existing_file, title)
        print(f"Video Uploaded: https://www.youtube.com/watch?v={video_id}")
    elif choice == "4":
        video_id = input("Enter YouTube Video ID: ")
        download_captions_downsub(video_id)
    elif choice == "5":
        existing_file = input("Enter video file path: ")
        video_id = upload_video(youtube, existing_file, title)
        print(f"Video Uploaded: https://www.youtube.com/watch?v={video_id}")
        download_captions_downsub(video_id)
    else:
        print("Invalid choice")

if __name__ == "__main__":
    main()
