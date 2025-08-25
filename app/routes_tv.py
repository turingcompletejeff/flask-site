from flask import Blueprint, render_template, request, redirect, url_for, flash, current_app, jsonify
from flask_login import login_user, logout_user, login_required, current_user
import requests
import json
from urllib.parse import quote
from config import Config

media_api = Blueprint('media_api',__name__,url_prefix="/tv/api")

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
        thumb_url = (f"/media/Items/{item_id}/Images/Primary"
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
    user_id = current_user.jellyfin_user_id

    # Fetch PlaybackInfo (includes MediaSources & MediaStreams)
    playback_info_url = f"{Config.JELLYFIN_URL}/Items/{item_id}/PlaybackInfo"
    headers = j_headers(token)
    payload = {
        "UserId": user_id,
        "StartTimeTicks": 0,
        "EnableDirectPlay": True,
        "EnableDirectStream": True,
        "EnableTranscoding": False,
        "IsPlayback": True,
        "AutoOpenLiveStream": False,
        "MediaSourceId": item_id,
        "MaxStreamingBitrate": 140000000
    }

    resp = requests.post(playback_info_url, headers=headers, json=payload, timeout=10)
    info = resp.json()

    print(json.dumps(info,indent=2))

    # Extract mediaSourceId
    media_source = info["MediaSources"][0]
    media_source_id = media_source["Id"]

    # Construct HLS master URL
    hls_url = (
        f"{Config.JELLYFIN_URL}/Videos/{item_id}/master.m3u8"
        f"?api_key={quote(token)}&mediaSourceId={media_source_id}"
        f"&AudioCodec=AAC"
    )

    # Extract subtitles directly from PlaybackInfo
    subs = []
    for s in media_source.get("MediaStreams", []):
        if s.get("Type") == "Subtitle":
            sid = s.get("Index")
            fmt = s.get("Codec", "srt").lower()
            url = (
                f"{Config.JELLYFIN_URL}/Videos/{item_id}/{sid}/Subtitles/{fmt}/stream.{fmt}"
                f"?api_key={quote(token)}"
            )
            subs.append({
                "label": s.get("DisplayTitle") or s.get("Language") or "Subtitles",
                "lang": s.get("Language"),
                "url": url
            })

    return jsonify({"hls_url": hls_url, "subtitles": subs})
