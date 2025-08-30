# main.py
import os
from flask import Flask, request, redirect
import spotipy
from spotipy.oauth2 import SpotifyOAuth

app = Flask(__name__)

# ====== CONFIGURAÇÃO DO SPOTIFY ======
# Você pode deixar os valores abaixo ou, de preferência,
# definir as variáveis de ambiente no Render:
# SPOTIFY_CLIENT_ID, SPOTIFY_CLIENT_SECRET, REDIRECT_URI

CLIENT_ID = os.getenv("SPOTIFY_CLIENT_ID", "7cb553bcc9504b03a00f05c7f87492db")
CLIENT_SECRET = os.getenv("SPOTIFY_CLIENT_SECRET", "137d5105ba574ed28aa9ca89ad216ae8")
REDIRECT_URI = os.getenv("REDIRECT_URI", "https://moodlist-backend.onrender.com/callback")

SCOPE = "user-library-read playlist-modify-public playlist-modify-private"

# open_browser=False evita o fluxo que usa raw_input (que quebrou no log)
sp_oauth = SpotifyOAuth(
    client_id=CLIENT_ID,
    client_secret=CLIENT_SECRET,
    redirect_uri=REDIRECT_URI,
    scope=SCOPE,
    open_browser=False,
    cache_path=None,   # sem cache de token no servidor
)

# ====== ROTAS ======

@app.route("/")
def home():
    return '<a href="/login">Login with Spotify</a>'

@app.route("/login")
def login():
    auth_url = sp_oauth.get_authorize_url()
    return redirect(auth_url)

@app.route("/callback")
def callback():
    # Spotify vai redirecionar pra cá com ?code=...
    code = request.args.get("code")
    if not code:
        return "Missing 'code' in callback.", 400

    try:
        # Pega o token sem tentar abrir navegador (resolve o erro do raw_input)
        token_info = sp_oauth.get_access_token(code=code, as_dict=True, check_cache=False)
        access_token = token_info["access_token"]

        # Exemplo: pegar usuário e criar uma playlist de teste
        sp = spotipy.Spotify(auth=access_token)
        me = sp.current_user()
        playlist = sp.user_playlist_create(
            user=me["id"],
            name="MoodList – Demo",
            public=False,
            description="Playlist criada automaticamente pelo MoodList (demo)."
        )

        return (
            f"<h2>Login successful!</h2>"
            f"<p>Logged in as: <b>{me.get('display_name') or me['id']}</b></p>"
            f"<p>Created playlist: <b>{playlist['name']}</b></p>"
            f"<p>You can close this tab now.</p>"
        )

    except Exception as e:
        # Mostra erro pra facilitar debug (e também aparece no log do Render)
        return f"Error during callback: {e}", 500


# ====== MODO LOCAL (opcional) ======
if __name__ == "__main__":
    port = int(os.getenv("PORT", 10000))
    app.run(host="0.0.0.0", port=port, debug=True)
