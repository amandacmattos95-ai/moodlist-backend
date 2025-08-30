import os
from flask import Flask, request, redirect, session, jsonify
import spotipy
from spotipy.oauth2 import SpotifyOAuth

# ----- Config -----
app = Flask(__name__)
app.secret_key = os.getenv("FLASK_SECRET", "change-me")  # defina FLASK_SECRET no Render

SPOTIPY_CLIENT_ID = os.getenv("7cb553bcc9504b03a00f05c7f87492db")
SPOTIPY_CLIENT_SECRET = os.getenv("062820ac33e64c9e84c59f9ffc806010")
SPOTIPY_REDIRECT_URI = os.getenv(
    "SPOTIPY_REDIRECT_URI",
    "https://moodlist-backend.onrender.com/callback",
)
SCOPE = "user-library-read playlist-modify-public playlist-modify-private"


def oauth():
    return SpotifyOAuth(
        client_id=SPOTIPY_CLIENT_ID,
        client_secret=SPOTIPY_CLIENT_SECRET,
        redirect_uri=SPOTIPY_REDIRECT_URI,
        scope=SCOPE,
    )


def get_spotify():
    """Pega o token da sessão e renova se precisar."""
    token_info = session.get("token_info")
    if not token_info:
        return None
    sp_oauth = oauth()
    if sp_oauth.is_token_expired(token_info):
        token_info = sp_oauth.refresh_access_token(token_info["refresh_token"])
        session["token_info"] = token_info
    return spotipy.Spotify(auth=token_info["access_token"])


# ----- Rotas -----
@app.route("/")
def home():
    return '<a href="/login">Login with Spotify</a>'


@app.route("/login")
def login():
    # opcional: para depois do login já executar uma ação
    next_url = request.args.get("next", "/done")
    session["next"] = next_url

    sp_oauth = oauth()
    auth_url = sp_oauth.get_authorize_url()
    return redirect(auth_url)


@app.route("/callback")
def callback():
    code = request.args.get("code")
    if not code:
        return "Error during callback: missing code", 400

    sp_oauth = oauth()
    # Pega e guarda o token na sessão
    token_info = sp_oauth.get_access_token(code)
    session["token_info"] = token_info

    # Mensagem de sucesso simples ou redireciona para a próxima ação
    next_url = session.pop("next", None)
    if next_url:
        return redirect(next_url)

    # Cria uma playlist de demonstração só para confirmar que funcionou
    sp = spotipy.Spotify(auth=token_info["access_token"])
    me = sp.current_user()
    pl = sp.user_playlist_create(
        me["id"], "MoodList – Demo", public=False, description="Created by MoodList"
    )
    return f"""
    <h2>Login successful!</h2>
    <p>Logged in as: {me.get("display_name")}</p>
    <p>Created playlist: <b>{pl['name']}</b></p>
    <p>You can close this tab now.</p>
    """


# --------- ENDPOINT: criar playlist ---------
@app.route("/create_playlist")
def create_playlist():
    sp = get_spotify()
    if not sp:
        return redirect("/login?next=/create_playlist")

    name = request.args.get("name", "MoodList – New")
    public = request.args.get("public", "false").lower() == "true"

    me = sp.current_user()
    pl = sp.user_playlist_create(
        me["id"], name, public=public, description="Made by MoodList"
    )

    return jsonify(
        {
            "playlist_id": pl["id"],
            "url": pl["external_urls"]["spotify"],
            "name": pl["name"],
        }
    )


# --------- ENDPOINT: adicionar músicas ---------
def normalize_tracks(tracks_param: str):
    parts = [p.strip() for p in tracks_param.split(",") if p.strip()]
    uris = []
    for p in parts:
        if "spotify.com/track/" in p:
            tid = p.split("track/")[1].split("?")[0]
            uris.append("spotify:track:" + tid)
        elif p.startswith("spotify:track:"):
            uris.append(p)
        else:
            # assume que é só o ID
            uris.append("spotify:track:" + p)
    return uris


@app.route("/add_songs")
def add_songs():
    sp = get_spotify()
    if not sp:
        return redirect("/login?next=" + request.full_path)

    playlist_id = request.args.get("playlist_id")
    tracks = request.args.get("tracks", "")

    if not playlist_id or not tracks:
        return "Use ?playlist_id=...&tracks=ID1,ID2 ou URLs do Spotify", 400

    uris = normalize_tracks(tracks)

    for i in range(0, len(uris), 100):
        sp.playlist_add_items(playlist_id, uris[i : i + 100])

    return jsonify({"added": len(uris), "playlist_id": playlist_id})


# --------- ENDPOINT: organizar biblioteca (simples) ---------
@app.route("/organize")
def organize():
    """Pega suas músicas salvas e cria uma playlist ordenada por energy+valence."""
    sp = get_spotify()
    if not sp:
        return redirect("/login?next=" + request.full_path)

    limit = int(request.args.get("limit", 500))
    me = sp.current_user()

    # carrega suas músicas salvas
    items = []
    offset = 0
    while len(items) < limit:
        batch = sp.current_user_saved_tracks(
            limit=min(50, limit - len(items)), offset=offset
        )["items"]
        if not batch:
            break
        items.extend(batch)
        offset += len(batch)

    track_ids = [it["track"]["id"] for it in items if it.get("track")]
    if not track_ids:
        return "No saved tracks found.", 400

    # ordena por energia + valence (bem simples e efetivo)
    feats = sp.audio_features(track_ids)
    scored = []
    for tid, f in zip(track_ids, feats):
        if not f:
            continue
        score = (f.get("energy") or 0) + (f.get("valence") or 0)
        scored.append((score, tid))
    scored.sort(reverse=True)
    ordered_ids = [tid for _, tid in scored]

    name = f"MoodList — Auto {min(limit, len(ordered_ids))}"
    pl = sp.user_playlist_create(
        me["id"], name, public=False, description="Auto-organized by energy+valence"
    )

    uris = ["spotify:track:" + tid for tid in ordered_ids]
    for i in range(0, len(uris), 100):
        sp.playlist_add_items(pl["id"], uris[i : i + 100])

    return jsonify(
        {
            "playlist_id": pl["id"],
            "url": pl["external_urls"]["spotify"],
            "count": len(uris),
            "name": pl["name"],
        }
    )


# --------- Render / Gunicorn ---------
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.getenv("PORT", "10000")))
