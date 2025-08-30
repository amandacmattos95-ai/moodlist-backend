from flask import Flask, request, redirect
import spotipy
from spotipy.oauth2 import SpotifyOAuth

app = Flask(__name__)

# 🔑 Suas credenciais do Spotify Developer
CLIENT_ID = "7cb553bcc9504b03a00f05c7f87492db"
CLIENT_SECRET = "7effe28a633644aaa1841e20b7f63acf"
REDIRECT_URI = "https://moodlist-backend.onrender.com/callback"

# 🎵 Configuração do OAuth
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
    try:
        code = request.args.get("code")
        token_info = sp_oauth.get_access_token(code)

        if token_info and "access_token" in token_info:
            access_token = token_info["access_token"]
            sp = spotipy.Spotify(auth=access_token)

            # pega o perfil do usuário
            user_profile = sp.current_user()

            # cria uma playlist de teste
            playlist = sp.user_playlist_create(
                user_profile["id"],
                "MoodList Test 🎵",
                public=True,
                description="Playlist criada automaticamente pelo MoodList"
            )

            return f"✅ Logado como {user_profile['display_name']}!<br>Playlist criada: <a href='{playlist['external_urls']['spotify']}' target='_blank'>{playlist['name']}</a>"
        else:
            return "❌ Erro: não consegui pegar o token de acesso."
    except Exception as e:
        return f"⚠️ Internal Error: {str(e)}"

if __name__ == '__main__':
    app.run(debug=True)
