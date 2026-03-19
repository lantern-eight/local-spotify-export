Spotify Playlist Exporter
Exports all your Spotify playlists to CSV files.
Columns: Playlist, Track #, Song Name, Artist(s), Album, Duration, Added Date

Setup:
  1. Create an app at https://developer.spotify.com/dashboard
  1. Set redirect URI to http://127.0.0.1:6820/callback
  1. Copy .env.example to .env and fill in your Client ID and Secret
  1. pip install -r requirements.txt
  1. python export_playlists.py
