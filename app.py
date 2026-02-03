"""
Transcript service for n8n Slack integration.
Fetches YouTube transcripts and metadata via HTTP API.
"""
from flask import Flask, jsonify, request
from youtube_transcript_api import YouTubeTranscriptApi
import urllib.request
import json
import re

app = Flask(__name__)


def extract_video_id(url_or_id: str) -> str:
    """Extract video ID from URL or return as-is if already an ID."""
    patterns = [
        r'(?:youtube\.com\/watch\?v=|youtu\.be\/|youtube\.com\/embed\/)([a-zA-Z0-9_-]{11})',
        r'^([a-zA-Z0-9_-]{11})$'
    ]
    for pattern in patterns:
        match = re.search(pattern, url_or_id)
        if match:
            return match.group(1)
    return url_or_id


@app.route('/transcript')
def transcript():
    """Get transcript for a YouTube video."""
    video_id = request.args.get('v', '')
    video_id = extract_video_id(video_id)
    timestamps = request.args.get('timestamps', 'false').lower() == 'true'

    if not video_id:
        return jsonify({'error': 'Missing video ID parameter "v"'}), 400

    try:
        # New API: use .fetch() on the transcript object
        ytt_api = YouTubeTranscriptApi()
        data = ytt_api.fetch(video_id)

        if timestamps:
            # Format with timestamps
            lines = []
            for entry in data:
                mins = int(entry.start // 60)
                secs = int(entry.start % 60)
                lines.append(f"[{mins}:{secs:02d}] {entry.text}")
            text = '\n'.join(lines)
        else:
            # Plain text
            text = ' '.join([x.text for x in data])

        return jsonify({
            'video_id': video_id,
            'transcript': text,
            'segments': len(data)
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 400


@app.route('/metadata')
def metadata():
    """Get metadata for a YouTube video via oEmbed."""
    video_id = request.args.get('v', '')
    video_id = extract_video_id(video_id)

    if not video_id:
        return jsonify({'error': 'Missing video ID parameter "v"'}), 400

    try:
        url = f'https://www.youtube.com/oembed?url=https://www.youtube.com/watch?v={video_id}&format=json'
        with urllib.request.urlopen(url, timeout=10) as response:
            data = json.loads(response.read().decode())

        return jsonify({
            'video_id': video_id,
            'title': data.get('title', ''),
            'channel': data.get('author_name', ''),
            'url': f'https://www.youtube.com/watch?v={video_id}'
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 400


@app.route('/health')
def health():
    """Health check endpoint."""
    return jsonify({'status': 'ok'})


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5001)
