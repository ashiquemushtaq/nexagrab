# app.py

from flask import Flask, request, jsonify, send_file, after_this_request
from flask_cors import CORS
from yt_dlp import YoutubeDL, DownloadError
import os
import re
import uuid # For generating unique filenames
import threading # For background cleanup
import time    # For delays

app = Flask(__name__)
CORS(app) # Enable CORS for all routes

# Directory to store temporarily downloaded videos on the server
DOWNLOAD_DIR = 'temp_downloads'
if not os.path.exists(DOWNLOAD_DIR):
    os.makedirs(DOWNLOAD_DIR)

# --- IMPORTANT: CONFIGURE FFMPEG LOCATION HERE ---
# Use the exact path you found for your ffmpeg.exe
FFMPEG_LOCATION = r'C:\ffmpeg\ffmpeg-2025-06-08-git-5fea5e3e11-full_build\bin\ffmpeg.exe'
# Note: The 'r' before the string means it's a raw string, which helps with backslashes on Windows.

# Function to safely delete files in a background thread (remains unchanged)
def delayed_file_cleanup(filepath, delay=5, retries=5):
    """
    Attempts to delete a file after a delay, with multiple retries,
    to handle file locking issues, especially on Windows.
    """
    for i in range(retries):
        try:
            time.sleep(delay) # Wait for a few seconds
            if os.path.exists(filepath):
                os.remove(filepath)
                print(f"Cleaned up temporary file: {filepath} after {i+1} attempt(s).")
                return # Success
        except OSError as e: # Catch OS errors (like file in use)
            print(f"Attempt {i+1} to delete {filepath} failed: {e}. Retrying...")
            delay *= 2 # Exponential backoff for next retry
        except Exception as e: # Catch any other unexpected errors
            print(f"Unexpected error during cleanup of {filepath}: {e}")
            return # Don't retry if it's not an OSError

    print(f"Failed to clean up {filepath} after {retries} attempts.")

# Helper function to get readable format labels (unchanged)
def get_format_label(f):
    """
    Generates a readable label for a given yt-dlp format dictionary.
    Prioritizes resolution, then format note, then extension, then filesize.
    Handles None values gracefully.
    """
    label_parts = []
    height = f.get('height')
    if height is not None:
        label_parts.append(f"{height}p")
    format_note = f.get('format_note')
    if format_note:
        label_parts.append(format_note)
    ext = f.get('ext')
    if ext:
        label_parts.append(ext)
    vcodec = f.get('vcodec')
    acodec = f.get('acodec')
    if vcodec != 'none' and acodec != 'none':
        label_parts.append("(Video + Audio)")
    elif vcodec == 'none' and acodec != 'none':
        label_parts.append("(Audio Only)")
    elif vcodec != 'none' and acodec == 'none':
        label_parts.append("(Video Only)")
    filesize_approx = f.get('filesize_approx')
    filesize = f.get('filesize')
    size_value = filesize_approx if filesize_approx is not None else filesize
    if size_value is not None:
        try:
            size_mb = float(size_value) / (1024 * 1024)
            label_parts.append(f"({size_mb:.2f} MB)")
        except (ValueError, TypeError):
            pass
    if not label_parts:
        return f.get('format_id', 'Unknown Quality')
    return " ".join(label_parts)


@app.route('/')
def home():
    """Basic route to confirm backend is running."""
    return "Video Downloader Backend is running!"

@app.route('/api/get-video-info', methods=['POST'])
def get_video_info():
    """
    Endpoint to fetch available video qualities (formats) for a given URL.
    Returns a list of quality objects with format_id and a readable label.
    """
    data = request.json
    video_url = data.get('url')

    if not video_url:
        return jsonify({'error': 'No URL provided'}), 400

    print(f"Fetching info for URL: {video_url}")

    try:
        ydl_opts_info = {
            'listformats': True,
            'simulate': True,
            'quiet': True,
            'no_warnings': True,
            'noplaylist': True,
            'skip_download': True,
            'ffmpeg_location': FFMPEG_LOCATION,
        }
        with YoutubeDL(ydl_opts_info) as ydl:
            info_dict = ydl.extract_info(video_url, download=False)

            available_qualities = []
            if 'formats' in info_dict:
                sorted_formats = sorted(
                    info_dict['formats'],
                    key=lambda f: (
                        f.get('preference') if f.get('preference') is not None else -1,
                        f.get('height') if f.get('height') is not None else 0,
                        f.get('tbr') if f.get('tbr') is not None else 0,
                        f.get('filesize_approx') if f.get('filesize_approx') is not None else 0,
                        f.get('filesize') if f.get('filesize') is not None else 0
                    ),
                    reverse=True
                )
                seen_labels = set()
                for f in sorted_formats:
                    if f.get('url') and f.get('protocol') not in ['m3u8_native', 'm3u8', 'dash', 'rtmp']:
                        if f.get('vcodec') != 'none' or f.get('acodec') != 'none':
                            label = get_format_label(f)
                            if label in seen_labels:
                                label = f"{label} (ID: {f['format_id']})"

                            available_qualities.append({
                                'format_id': f['format_id'],
                                'label': label,
                                'ext': f.get('ext'),
                                'title': info_dict.get('title', 'video')
                            })
                            seen_labels.add(label)
            
            if not available_qualities and 'url' in info_dict and info_dict.get('vcodec') != 'none':
                label = get_format_label(info_dict)
                available_qualities.append({
                    'format_id': 'best',
                    'label': label or "Best Quality (Direct Link)",
                    'ext': info_dict.get('ext'),
                    'title': info_dict.get('title', 'video')
                })

            if not available_qualities:
                 return jsonify({'error': 'No suitable downloadable formats found.'}), 500

            return jsonify({'qualities': available_qualities})

    except DownloadError as e:
        print(f"yt-dlp DownloadError for {video_url}: {e}")
        if "Unsupported URL" in str(e):
            return jsonify({'error': 'Unsupported platform or invalid video URL.'}), 400
        if "Private video" in str(e) or "Login required" in str(e):
             return jsonify({'error': 'Video is private or requires login.'}), 403
        return jsonify({'error': f'Could not retrieve video information: {str(e)}'}), 500
    except Exception as e:
        print(f"General error fetching video info for {video_url}: {e}")
        return jsonify({'error': f'An unexpected error occurred: {str(e)}'}), 500


# --- MODIFIED: Allow GET requests for /api/get-download-link ---
@app.route('/api/get-download-link', methods=['GET', 'POST'])
def get_download_link():
    """
    Endpoint to download the video on the server and then serve it to the client
    for direct download. This ensures video and audio merging if necessary.
    Accepts both GET (for browser redirect) and POST (for API calls).
    """
    if request.method == 'POST':
        data = request.json
    else: # GET request, parameters are in args
        data = request.args

    video_url = data.get('url')
    format_id = data.get('format_id')
    suggested_filename_base = data.get('filename_hint', 'video_download')
    
    if not video_url or not format_id:
        return jsonify({'error': 'URL or format ID not provided'}), 400

    print(f"Attempting to download and serve URL: {video_url}, Format ID: {format_id}")

    temp_filepath = None
    try:
        output_template = os.path.join(DOWNLOAD_DIR, f"{uuid.uuid4()}_%(title)s.%(ext)s")
        
        ydl_opts_download = {
            'format': f"{format_id}+bestaudio/bestvideo+bestaudio/best",
            'outtmpl': output_template,
            'noplaylist': True,
            'quiet': True,
            'no_warnings': True,
            'ffmpeg_location': FFMPEG_LOCATION,
            'merge_output_format': 'mp4', # Force MP4 merge if streams are separate
        }
        
        with YoutubeDL(ydl_opts_download) as ydl:
            info_dict = ydl.extract_info(video_url, download=True)
            
            # Find the path to the downloaded/merged file
            if 'filepath' in info_dict:
                temp_filepath = info_dict['filepath']
            elif 'requested_downloads' in info_dict and info_dict['requested_downloads']:
                if isinstance(info_dict['requested_downloads'][0], dict) and 'filepath' in info_dict['requested_downloads'][0]:
                    temp_filepath = info_dict['requested_downloads'][0]['filepath']
                elif isinstance(info_dict['requested_downloads'][0], str):
                    temp_filepath = info_dict['requested_downloads'][0]
            
            if not temp_filepath:
                raise Exception("yt-dlp did not provide a valid downloaded file path.")

            if not os.path.exists(temp_filepath):
                raise Exception(f"Downloaded file not found at: {temp_filepath}")

            title = info_dict.get('title', 'video')
            clean_title = re.sub(r'[\\/:*?"<>|]', '', title)
            clean_title = re.sub(r'\s+', '_', clean_title).strip('_')
            
            file_extension = os.path.splitext(temp_filepath)[1]
            
            download_name = f"{clean_title}{file_extension}"
            if not download_name:
                download_name = f"video_{uuid.uuid4().hex}{file_extension}"

            print(f"Preparing for direct download: {temp_filepath} as {download_name}")

            # Trigger delayed cleanup in a separate thread
            cleanup_thread = threading.Thread(target=delayed_file_cleanup, args=(temp_filepath,))
            cleanup_thread.daemon = True
            cleanup_thread.start()

            return send_file(
                temp_filepath,
                mimetype=f'video/{file_extension.lstrip(".")}', # Keep mimetype for browser info
                as_attachment=True, # Crucial for direct download
                download_name=download_name # Suggest filename to browser
            )

    except DownloadError as e:
        print(f"yt-dlp DownloadError during download for {video_url} (format {format_id}): {e}")
        if temp_filepath and os.path.exists(temp_filepath):
            try:
                os.remove(temp_filepath)
                print(f"Cleaned up partial file due to error: {temp_filepath}")
            except Exception as clean_e:
                print(f"Error during cleanup of partial file {temp_filepath}: {clean_e}")
        if "Unsupported URL" in str(e):
            return jsonify({'error': 'Unsupported platform or invalid video URL.'}), 400
        if "Private video" in str(e) or "Login required" in str(e):
             return jsonify({'error': 'Video is private or requires login.'}), 403
        return jsonify({'error': f'Failed to process video: {str(e)}'}), 500
    except Exception as e:
        print(f"General error during get download link request for {video_url} (format {format_id}): {e}")
        if temp_filepath and os.path.exists(temp_filepath):
            try:
                os.remove(temp_filepath)
                print(f"Cleaned up partial file due to error: {temp_filepath}")
            except Exception as clean_e:
                print(f"Error during cleanup of partial file {temp_filepath}: {clean_e}")
        # Return a JSON error response instead of letting the server crash or return plain text
        return jsonify({'error': f'An unexpected error occurred during processing: {str(e)}'}), 500

if __name__ == '__main__':
    app.run(debug=True, port=5000)