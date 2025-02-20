import requests
from youtube_transcript_api import YouTubeTranscriptApi
import json

API_KEY = "AIzaSyBIKHx6j2-XFHLoPqkMSIBiAVybFlUPPXI"
CHANNEL_ID = "UChCqE3MptBJlubiJMFxVnlw"  

# Fetch YouTube videos from channel
search_url = f"https://www.googleapis.com/youtube/v3/search?key={API_KEY}&channelId={CHANNEL_ID}&part=snippet&type=video&maxResults=100000"
videos = requests.get(search_url).json().get("items", [])

# Process each video and retrieve full transcript
video_data = []

for video in videos:
    video_id = video["id"]["videoId"]
    title = video["snippet"]["title"]
    url = f"https://www.youtube.com/watch?v={video_id}"
    published_at = video["snippet"]["publishedAt"]

    # Extract full transcript with timestamps
    try:
        transcript_data = YouTubeTranscriptApi.get_transcript(video_id)
        transcript = "\n".join([f"{entry['start']}s: {entry['text']}" for entry in transcript_data])
    except:
        transcript = "No transcript available"

    # Convert to Weaviate format
    weaviate_object = {
        "class": "YouTubeVideo",
        "properties": {
            "title": title,
            "videoId": video_id,
            "url": url,
            "publishedAt": published_at,
            "transcript": transcript
        }
    }

    video_data.append(weaviate_object)

# Save data to a JSON file
json_path = "YouTube_Data.json"
with open(json_path, "w", encoding="utf-8") as f:
    json.dump(video_data, f, indent=4)

print(f"✅ Data saved to {json_path}")