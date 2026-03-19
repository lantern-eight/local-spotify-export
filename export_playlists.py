#!/usr/bin/env python3
"""
Spotify Playlist Exporter
Exports all your Spotify playlists to CSV files.
Columns: Playlist, Track #, Song Name, Artist(s), Album, Duration, Added Date

Setup:
  1. Create an app at https://developer.spotify.com/dashboard
  2. Set redirect URI to http://127.0.0.1:6820/callback
  3. Copy .env.example to .env and fill in your Client ID and Secret
  4. pip install -r requirements.txt
  5. python export_playlists.py
"""

import csv
import os
import sys
from datetime import datetime, timedelta

import spotipy
from dotenv import load_dotenv
from spotipy.oauth2 import SpotifyOAuth

load_dotenv()

CLIENT_ID = os.getenv("SPOTIPY_CLIENT_ID")
CLIENT_SECRET = os.getenv("SPOTIPY_CLIENT_SECRET")
REDIRECT_URI = os.getenv("SPOTIPY_REDIRECT_URI", "http://127.0.0.1:6820/callback")
SCOPE = "playlist-read-private playlist-read-collaborative"

OUTPUT_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "exports")


def get_spotify_client():
    if not CLIENT_ID or not CLIENT_SECRET:
        print("Error: Missing SPOTIPY_CLIENT_ID or SPOTIPY_CLIENT_SECRET in .env")
        print("See .env.example for setup instructions.")
        sys.exit(1)

    return spotipy.Spotify(auth_manager=SpotifyOAuth(
        client_id=CLIENT_ID,
        client_secret=CLIENT_SECRET,
        redirect_uri=REDIRECT_URI,
        scope=SCOPE,
        cache_path=os.path.join(os.path.dirname(os.path.abspath(__file__)), ".spotify_cache"),
        open_browser=True,
    ))


def get_all_playlists(sp):
    """Fetch all playlists for the current user, handling pagination."""
    playlists = []
    results = sp.current_user_playlists(limit=50)
    while results:
        playlists.extend(results["items"])
        results = sp.next(results) if results["next"] else None
    return playlists


def get_playlist_tracks(sp, playlist_id):
    """Fetch all tracks from a playlist, handling pagination."""
    tracks = []
    results = sp.playlist_items(
        playlist_id,
        limit=100,
    )
    while results:
        tracks.extend(results["items"])
        results = sp.next(results) if results["next"] else None
    return tracks


def format_duration(ms):
    """Convert milliseconds to M:SS format."""
    d = timedelta(milliseconds=ms)
    total_seconds = int(d.total_seconds())
    minutes = total_seconds // 60
    seconds = total_seconds % 60
    return f"{minutes}:{seconds:02d}"


def export_playlists():
    sp = get_spotify_client()
    user = sp.current_user()
    print(f"Logged in as: {user['display_name']}")

    os.makedirs(OUTPUT_DIR, exist_ok=True)
    date_stamp = datetime.now().strftime("%Y-%m-%d")

    user_id = user["id"]
    playlists = get_all_playlists(sp)
    print(f"Found {len(playlists)} playlists\n")

    # Write CSV progressively so data isn't lost on errors
    output_file = os.path.join(OUTPUT_DIR, "spotify_playlists.csv")
    fieldnames = ["Playlist", "Playlist Owner", "Track #", "Song Name",
                   "Artist(s)", "Album", "Duration", "Date Added"]
    total_tracks = 0
    skipped = []

    with open(output_file, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()

        for playlist in playlists:
            if not playlist:
                continue
            name = playlist["name"]
            playlist_id = playlist["id"]
            owner_id = playlist["owner"]["id"]
            owner = playlist["owner"]["display_name"]
            if owner_id != user_id:
                print(f"  Skipping: {name} (owned by {owner})")
                continue
            track_info = playlist.get("tracks") or playlist.get("items")
            total = track_info["total"] if isinstance(track_info, dict) and "total" in track_info else "?"
            print(f"  Exporting: {name} ({total} tracks, by {owner})")

            try:
                tracks = get_playlist_tracks(sp, playlist_id)
            except spotipy.exceptions.SpotifyException as e:
                print(f"    Skipped: {e.http_status} error")
                skipped.append(name)
                continue

            for i, item in enumerate(tracks, 1):
                track = item.get("track") or item.get("item")
                if not track:
                    continue

                artists = ", ".join(a["name"] for a in track["artists"])
                added_at = item.get("added_at", "")[:10]  # YYYY-MM-DD

                writer.writerow({
                    "Playlist": name,
                    "Playlist Owner": owner,
                    "Track #": i,
                    "Song Name": track["name"],
                    "Artist(s)": artists,
                    "Album": track["album"]["name"],
                    "Duration": format_duration(track["duration_ms"]),
                    "Date Added": added_at,
                })
                total_tracks += 1

    print(f"\nDone! Exported {total_tracks} tracks from {len(playlists)} playlists")
    if skipped:
        print(f"Skipped {len(skipped)} playlists (access denied): {', '.join(skipped)}")
    print(f"Output: {output_file}")


if __name__ == "__main__":
    export_playlists()
