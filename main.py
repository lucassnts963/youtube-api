import os
import uuid

from flask import Flask, request, jsonify, send_file
from pytube import YouTube, Playlist
from io import BytesIO

app = Flask(__name__)

def generate_unique_folder_name():
  return str(uuid.uuid4())

@app.route('/')
def index():
  return send_file('index.html')

@app.route('/video_info')
def video_info():
  try:
    url = request.args.get('url')
    yt = YouTube(url)
    video_info = {
      'title': yt.title,
      'author': yt.author,
      'duration': yt.length,
      'thumbnail_url': yt.thumbnail_url,
      'views': yt.views,
      'video_details': yt.vid_info['videoDetails']
    }

    return jsonify(video_info)
  except Exception as e:
    return jsonify({ 'error': str(e) }), 400

@app.route('/download_audio', methods=['GET', 'POST'])
def download_audio():
  try:
    url = request.args.get('url')
    yt = YouTube(url)
    audio_stream = yt.streams.get_audio_only()
    buffer = BytesIO()
    audio_stream.stream_to_buffer(buffer)
    buffer.seek(0)

    return send_file(buffer, as_attachment=True, download_name=f'{yt.title}.mp3')
  except Exception as e:
    return jsonify({ 'error': str(e) }), 400

@app.route('/download_playlist', methods=['GET', 'POST'])
def download_playlist():
  try:
    url = request.args.get('url')
    pl = Playlist(url)

    folder_name = generate_unique_folder_name()
    temp_folder = os.path.join('temp', folder_name)
    os.makedirs(temp_folder, exist_ok=True)

    for link in pl:
      yt = YouTube(link)
      audio_stream = yt.streams.filter(only_audio=True).first()
      audio_filename = f'{yt.title}.mp3'
      audio_stream.download(output_path=temp_folder, filename=audio_filename)
    
    zip_filename = f'{folder_name}.zip'
    os.system(f'zip -j {zip_filename} {temp_folder}/*')

    response = send_file(zip_filename, as_attachment=True)

    os.remove(zip_filename)

    for file in os.listdir(temp_folder):
      file_path = os.path.join(temp_folder, file)
      os.remove(file_path)
    os.rmdir(temp_folder)

    return response
  except Exception as e:
    return jsonify({ 'error': str(e) }), 400

if __name__ == '__main__':
  app.run(debug=False, port=8000, host='0.0.0.0')