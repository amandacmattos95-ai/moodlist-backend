import os
from flask import Flask, request, redirect, url_for, session
import spotipy
from spotipy.oauth2 import SpotifyOAuth

# Configurações do Spotify com variáveis de ambiente
CLIENT_ID = os.getenv("SPOTIPY_CLIENT_ID")
CLIENT_SECRET = os.getenv("SPOTIPY_CLIENT_SECRET")
REDIRECT_URI = os.getenv("SPOTIPY_REDIRECT_URI", "https://moodlist-backend.onrender.com/callback")
SCOPE = "user-library-read playlist-modify-public playlist-modify-private"

app = Flask(__name__)
app.secret_key = os.getenv("FLASK_SECRET_KEY", "change-me")

sp_oauth = SpotifyOAuth(
    client_id=CLIENT_ID,
    client_secret=CLIENT_SECRET,
    redirect_uri=REDIRECT_URI,
    scope=SCOPE
)

@app.route('/')
def index():
    return '<a href="/login">Login with Spotify</a>'

@app.route('/login')
def login():
    auth_url = sp_oauth.get_authorize_url()
    return redirect(auth_url)

@app.route('/callback')
def callback():
    code = request.args.get('code')
    if code:
        try:
            token_info = sp_oauth.get_access_token(code)
            access_token = token_info['access_token']

            sp = spotipy.Spotify(auth=access_token)
            user_info = sp.current_user()
            user_name = user_info['display_name']

            # Cria uma playlist de exemplo
            playlist = sp.user_playlist_create(user=user_info['id'], name='MoodList – Demo', public=False)

            return f"""
                <h1>Login successful!</h1>
                <p>Logged in as: <strong>{user_name}</strong></p>
                <p>Created playlist: <strong>{playlist['name']}</strong></p>
                <p>You can close this tab now.</p>
            """
        except Exception as e:
            return f"Error getting access token: {str(e)}"
    else:
        return "Error during callback: missing code"

if __name__ == '__main__':
    app.run(debug=True)
