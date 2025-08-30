from flask import Flask, request, redirect
import spotipy
from spotipy.oauth2 import SpotifyOAuth

app = Flask(__name__)

CLIENT_ID = "7cb553bcc9504b03a00f05c7f87492db"
CLIENT_SECRET = "7effe28a633644aaa1841e20b7f63acf"
REDIRECT_URI = "https://moodlist-backend.onrender.com/callback"

sp_oauth = SpotifyOAuth(
    client_id=CLIENT_ID,
    client_secret=CLIENT_SECRET,
    redirect_uri=REDIRECT_URI,
    scope="user-library-read playlist-modify-public playlist-modify-private"
)

@app.route('/')
def home():
    return '<a href="/login">Login with Spotify</a>'

@app.route('/login')
def login():
    auth_url = sp_oauth.get_authorize_url()
    return redirect(auth_url)

@app.route('/callback')
def callback():
    code = request.args.get("code")
    token_info = sp_oauth.get_access_token(code)
    access_token = token_info['access_token']

    sp = spotipy.Spotify(auth=access_token)
    user_profile = sp.current_user()
    return f"Hello, {user_profile['display_name']}! 🎵"
# Necessário para rodar no Render
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
