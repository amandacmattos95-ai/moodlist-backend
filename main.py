import os
from flask import Flask, request, redirect, url_for, session
import spotipy
from spotipy.oauth2 import SpotifyOAuth

# ===== Config =====
CLIENT_ID = os.getenv("7cb553bcc9504b03a00f05c7f87492db")
CLIENT_SECRET = os.getenv("b440fecdc37049d4ad1ec5dc19970375")
REDIRECT_URI = os.getenv("REDIRECT_URI", "https://moodlist-backend.onrender.com/callback")
SCOPE = "user-library-read playlist-modify-public playlist-modify-private"

app = Flask(__name__)
app.secret_key = os.getenv("FLASK_SECRET_KEY", "change-me")

def make_oauth():
    # Logs de diagnóstico no console do Render (não expostos ao usuário)
    masked = (CLIENT_ID[:6] + "..." + CLIENT_ID[-4:]) if CLIENT_ID else "MISSING"
    app.logger.info(f"[OAuth] Using CLIENT_ID={masked} | REDIRECT_URI={REDIRECT_URI}")
    return SpotifyOAuth(
        client_id=CLIENT_ID,
        client_secret=CLIENT_SECRET,
        redirect_uri=REDIRECT_URI,
        scope=SCOPE,
        show_dialog=True  # força a tela de consentimento, útil para testes
    )

@app.route("/")
def home():
    return '<a href="/login">Login with Spotify</a>'

@app.route("/login")
def login():
    sp_oauth = make_oauth()
    auth_url = sp_oauth.get_authorize_url()
    app.logger.info(f"[Login] Redirecting to Spotify auth URL")
    return redirect(auth_url)

@app.route("/callback")
def callback():
    # Tratativas de erro padrão
    if request.args.get("error"):
        err = request.args.get("error")
        desc = request.args.get("error_description", "")
        app.logger.error(f"[Callback] Spotify returned error: {err} {desc}")
        return f"Error during callback: {err} {desc}"

    code = request.args.get("code")
    if not code:
        app.logger.error("[Callback] Missing 'code' parameter")
        return "Error during callback: missing code"

    sp_oauth = make_oauth()

    try:
        # Spotipy 2.23 às vezes retorna dict, às vezes string; tratamos ambos
        token_info = sp_oauth.get_access_token(code, as_dict=True)
        if isinstance(token_info, str):
            # fallback para versões antigas
            token_info = {"access_token": token_info}
        access_token = token_info.get("access_token")
        if not access_token:
            app.logger.error(f"[Callback] No access_token in token_info: {token_info}")
            return "Error during callback: no access token"
    except Exception as e:
        app.logger.exception(f"[Callback] Error getting access token: {e}")
        return f"Error getting access token: {e}"

    try:
        sp = spotipy.Spotify(auth=access_token)
        me = sp.current_user()
        user_name = me.get("display_name") or me.get("id")

        # cria uma playlist de teste para validar permissão
        playlist = sp.user_playlist_create(
            me["id"],
            "MoodList – Demo",
            public=False,
            description="Created by MoodList demo"
        )
        pl_name = playlist.get("name", "MoodList – Demo")
        app.logger.info(f"[Callback] Login OK. Created playlist: {pl_name}")

        return (
            "<h2>Login successful!</h2>"
            f"<p>Logged in as: <b>{user_name}</b></p>"
            f"<p>Created playlist: <b>{pl_name}</b></p>"
            "<p>You can close this tab now.</p>"
        )
    except Exception as e:
        app.logger.exception(f"[Callback] Error creating playlist: {e}")
        return f"Error after login: {e}"

@app.route("/health")
def health():
    ok = all([CLIENT_ID, CLIENT_SECRET, REDIRECT_URI])
    return ("OK" if ok else "MISSING_ENV"), 200 if ok else 500

if __name__ == "__main__":
    # Útil para rodar local, no Render o gunicorn chama app:app
    app.run(host="0.0.0.0", port=int(os.getenv("PORT", 5000)))
