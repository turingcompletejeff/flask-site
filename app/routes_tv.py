from flask import Blueprint, render_template, request, redirect, url_for, flash, current_app
from flask_login import login_user, logout_user, login_required
import requests
from urllib.parse import quote

media_api = Blueprint('media_api',__name__,url_prefix="/media/api")

def j_headers(token):
    return {"X-Emby-Token": token}

@media_api.get("/items")
@login_required
def list_items():
    """
    Returns a simple list of items for the logged-in user.
    Expect current_user.jellyfin_user_id and current_user.jellyfin_session_token to be set.
    """
    uid = current_user.jellyfin_user_id
    token = current_user.jellyfin_session_token

    # Movies + Episodes; tweak IncludeItemTypes as needed
    r = requests.get(
        f"{Config.JELLYFIN_URL}/Users/{uid}/Items",
        params={"IncludeItemTypes":"Movie,Episode","Recursive":"true","SortBy":"SortName"},
        headers=j_headers(token),
        timeout=10
    )
    r.raise_for_status()
    data = r.json().get("Items", [])

    items = []
    for it in data:
        item_id = it.get("Id")
        # Prefer Primary image; fallback to Thumb
        thumb_url = (f"/media/proxy/Items/{item_id}/Images/Primary"
                     f"?w=400&quality=90")  # served via a lightweight proxy route (optional)

        items.append({
            "id": item_id,
            "name": it.get("Name"),
            "year": it.get("ProductionYear"),
            "overview": it.get("Overview"),
            "runtime": (it.get("RunTimeTicks") or 0) // 10_000_000,  # seconds
            "type": it.get("Type"),
            "thumb_url": thumb_url
        })

    return jsonify(items)

@media_api.get("/hls/<item_id>")
@login_required
def hls_for_item(item_id):
    """
    Returns a per-user tokenized HLS master URL and optional subtitle tracks.
    """
    token = current_user.jellyfin_session_token

    # Option A (simple): always use master.m3u8
    hls_url = f"{Config.JELLYFIN_URL}/Videos/{item_id}/master.m3u8?api_key={quote(token)}"

    # Optionally enumerate external subtitles
    subs = []
    # Ask Jellyfin for media info (to find subtitle tracks)
    r = requests.get(f"{Config.JELLYFIN_URL}/Items/{item_id}", headers=j_headers(token), timeout=10)
    if r.ok:
        streams = r.json().get("MediaStreams", [])
        for s in streams:
            if s.get("Type") == "Subtitle":
                # Build a direct subtitle stream URL
                sid = s.get("Index")
                fmt = (s.get("Codec") or "vtt").lower()
                # Jellyfin supports /Subtitles/{Format}/stream.{Format}
                url = f"{Config.JELLYFIN_URL}/Videos/{item_id}/{sid}/Subtitles/{fmt}/stream.{fmt}?api_key={quote(token)}"
                subs.append({"label": s.get("DisplayTitle") or s.get("Language") or "Subtitles", "lang": s.get("Language"), "url": url})

    return jsonify({"hls_url": hls_url, "subtitles": subs})