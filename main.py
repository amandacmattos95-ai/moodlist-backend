import os
from flask import Flask, request, redirect
import spotipy
from spotipy.oauth2 import SpotifyOAuth

# ===== Config (lê as variáveis do Render) =====
CLIENT_ID = os.getenv("SPOTIPY_CLIENT_ID")
CLIENT_SECRET = os.getenv("SPOTIPY_CLIENT_SECRET")
REDIRECT_URI = os.getenv("SPOTIPY_REDIRECT_URI", "https://moodlist-backend.onrender.com/callback")
SCOPE = "user-library-read playlist-modify-public playlist-modify-private"

app = Flask(__name__)
app.secret_key = os.getenv("FLASK_SECRET_KEY", "change-me")

def make_oauth():
    # Helper que cria o objeto de OAuth com seus dados
    return SpotifyOAuth(
        client_id=CLIENT_ID,
        client_secret=CLIENT_SECRET,
        redirect_uri=REDIRECT_URI,
        scope=SCOPE,
        show_dialog=True
    )

@app.route("/")
def home():
    return '<a href="/login">Login with Spotify</a>'

@app.route("/login")
def login():
    sp_oauth = make_oauth()
    auth_url = sp_oauth.get_authorize_url()
    return redirect(auth_url)

@app.route("/callback")
def callback():
    # Tratando erros vindos do Spotify
    if request.args.get("error"):
        err = request.args.get("error", "")
        desc = request.args.get("error_description", "")
        return f"Error during callback: {err}, {desc}"

    code = request.args.get("code")
    if not code:
        return "Error during callback: missing code"

    sp_oauth = make_oauth()

    try:
        # Versões diferentes do spotipy podem retornar dict/string. Forçamos dict.
        token_info = sp_oauth.get_access_token(code, as_dict=True)
    except Exception as e:
        return f"Error getting access token: {e}"

    access_token = token_info.get("access_token") if isinstance(token_info, dict) else None
    if not access_token:
        return "Error during callback: no access token"

    # Teste simples: pega usuário e cria uma playlist privada
    sp = spotipy.Spotify(auth=access_token)
    me = sp.current_user()
    user_name = me.get("display_name") or me.get("id")

    playlist = sp.user_playlist_create(
        me["id"],
        "MoodList – Demo",
        public=False,
        description="created by MoodList demo"
    )
    pl_name = playlist.get("name", "(no name)")

    return (
        f"<h2>Login successful!</h2>"
        f"<p>Logged in as: <b>{user_name}</b></p>"
        f"<p>Created playlist: <b>{pl_name}</b></p>"
        f"<p>You can close this tab now.</p>"
    )

@app.route("/health")
def health():
    ok = all([CLIENT_ID, CLIENT_SECRET, REDIRECT_URI])
    return ("OK" if ok else "MISSING_ENV"), 200 if ok else 500

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.getenv("PORT", "5000")))
