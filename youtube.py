from flask import Flask, request, jsonify, render_template_string
from googleapiclient.discovery import build
import re

app = Flask(__name__)

# Set your API key
API_KEY = 'AIzaSyAmL7zeQ67_e6ncVOlCuER-uSfT7LubHcs'

# Set the YouTube API service
youtube = build('youtube', 'v3', developerKey=API_KEY)

def extract_timestamps(video_id):
    # Call the videos.list method to retrieve details about the video including timestamps
    video_response = youtube.videos().list(
        id=video_id,
        part='snippet,contentDetails'
    ).execute()

    # Extract timestamps from the video description
    description = video_response['items'][0]['snippet']['description']
    pattern = r'(\d{1,2}:\d{2})'
    timestamps = re.findall(pattern, description)
    return timestamps

def extract_video_id(video_url):
    # Extract the video ID from the YouTube URL
    video_id = None
    if 'youtube.com' in video_url or 'youtu.be' in video_url:
        video_id = video_url.split('/')[-1].split('?')[0]
    return video_id

@app.route('/extract_timestamps', methods=['GET'])
def extract_timestamps_route():
    video_url = request.args.get('url')
    video_id = extract_video_id(video_url)
    timestamps = extract_timestamps(video_id)
    return render_template_string('''
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>YouTube Video Timestamps</title>
    </head>
    <body>
        <h1>YouTube Video Timestamps</h1>
        <div id="timestamps">
            <ul>
                {% for timestamp in timestamps %}
                <li>{{ timestamp }}</li>
                {% endfor %}
            </ul>
        </div>
    </body>
    </html>
    ''', timestamps=timestamps)

if __name__ == '__main__':
    app.run(debug=True)
