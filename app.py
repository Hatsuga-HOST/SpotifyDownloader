from flask import Flask, render_template, request, send_file
import requests, yt_dlp, os, base64, io, random, string
from config import CLIENT_ID, CLIENT_SECRET

app = Flask(__name__)

def generate_filename(length=8):
    return ''.join(random.choices(string.ascii_lowercase + string.digits, k=length))

def get_spotify_token():
    auth_string = f"{CLIENT_ID}:{CLIENT_SECRET}"
    auth_bytes = auth_string.encode("utf-8")
    auth_base64 = base64.b64encode(auth_bytes).decode("utf-8")

    headers = {
        "Authorization": f"Basic {auth_base64}",
        "Content-Type": "application/x-www-form-urlencoded"
    }

    data = {
        "grant_type": "client_credentials"
    }

    response = requests.post("https://accounts.spotify.com/api/token", headers=headers, data=data)
    token = response.json()['access_token']
    return token

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/result', methods=['POST'])
def result():
    spotify_link = request.form['spotify_url']
    track_id = spotify_link.split("/")[-1].split("?")[0]

    token = get_spotify_token()
    headers = {
        "Authorization": f"Bearer {token}"
    }

    res = requests.get(f"https://api.spotify.com/v1/tracks/{track_id}", headers=headers)
    if res.status_code != 200:
        return "Gagal ambil data dari Spotify."

    data = res.json()
    title = data['name']
    artist = data['artists'][0]['name']
    image = data['album']['images'][0]['url']
    query = f"{title} {artist}"

    return render_template('result.html', title=title, artist=artist, image=image, query=query)
@app.route('/download', methods=['POST'])
def download():
    query = request.form['query']
    random_name = generate_filename()

    ydl_opts = {
        'format': 'bestaudio/best',
        'outtmpl': f'{random_name}.%(ext)s',
        'quiet': True,
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
        }],
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(f"ytsearch:{query}", download=True)
            output_filename = ydl.prepare_filename(info['entries'][0]).replace(".webm", ".mp3").replace(".m4a", ".mp3")

        # Baca langsung ke memory
        with open(output_filename, 'rb') as f:
            mp3_data = io.BytesIO(f.read())

        os.remove(output_filename)  # Auto hapus biar gak nyangkut di folder

        mp3_data.seek(0)
        return send_file(
            mp3_data,
            mimetype='audio/mpeg',
            as_attachment=True,
            download_name=f"{random_name}.mp3"
        )

    except Exception as e:
        return f"Gagal download MP3: {str(e)}"

@app.route('/download-image', methods=['POST'])
def download_image():
    image_url = request.form['image_url']
    random_name = generate_filename()

    try:
        img_data = requests.get(image_url).content
        img_io = io.BytesIO(img_data)
        img_io.seek(0)

        return send_file(
            img_io,
            mimetype='image/jpeg',
            as_attachment=True,
            download_name=f"{random_name}_cover.jpg"
        )
    except Exception as e:
        return f"Gagal download gambar: {str(e)}"

if __name__ == '__main__':
    app.run(debug=True)
