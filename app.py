# Import necessary libraries
import os
import re
import sqlite3
import collections
from flask import Flask, render_template, redirect, request
import spotipy

# Instantiate Flask web app
app = Flask(__name__)

# Pull Spotify API credientials
username = os.environ.get('username')
client_id = os.environ.get('client_id')
client_secret = os.environ.get('client_secret')
redirect_uri = "https://spin-database.herokuapp.com"

# Instantiate SQL database
sqliteConnection = sqlite3.connect('spin.db', check_same_thread=False)
cursor = sqliteConnection.cursor()

# Reload tables at each update
cursor.execute("DROP TABLE IF EXISTS playlists")
cursor.execute("DROP TABLE IF EXISTS artists")
cursor.execute("DROP TABLE IF EXISTS tracks")

# Create tables for playlists, tracks, artists
playlists_table = """CREATE TABLE IF NOT EXISTS playlists (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                spotify_id TEXT,
                name TEXT NOT NULL,
                date TEXT NOT NULL,
                length TEXT NOT NULL,
                tracks TEXT
            )"""

tracks_table = """CREATE TABLE IF NOT EXISTS tracks (
                track_id TEXT,
                name TEXT,
                artist TEXT,
                count INTEGER
            )"""

artists_table = """CREATE TABLE IF NOT EXISTS artists (
                name TEXT,
                count INTEGER
            )"""

cursor.execute(playlists_table)
cursor.execute(tracks_table)
cursor.execute(artists_table)

# Landing page. Redirects to Spotify Authorization if not logged. If logged in, continues directly to homepage
@app.route('/')
def root():
    auth_manager = spotipy.oauth2.SpotifyOAuth(client_id=client_id, client_secret=client_secret, redirect_uri=redirect_uri)

    if request.args.get("code"):
        auth_manager.get_access_token(request.args.get("code"))
        return redirect("/index")

    else:
        auth_url = auth_manager.get_authorize_url()
        return render_template("root.html", auth_url=auth_url)

# Dummy page. Interacts with Spotify API to extract data, then pushes to home page.
@app.route('/index')
def index():
    auth_manager = spotipy.oauth2.SpotifyOAuth(client_id=client_id, client_secret=client_secret, redirect_uri=redirect_uri)

    sp = spotipy.Spotify(auth_manager=auth_manager)
    spin_playlists = []
    all_tracks = []
    all_artists = []

    # Checks if the playlist is for spin (all spin playlists start with the date first used)   
    spin = re.compile(r'\d+/')
    offset = 0

    # Spotipy limits playlist pulls to 50 at one time. Offset is used to be able to loop through all playlists. Needs to be adjusted in future if number of playlists exceeds 250.
    while offset <= 250:
        for playlist in sp.user_playlists(username,offset=offset)['items']:
            if spin.match(playlist['name']):
                key_data = {}
                key_data['spotify_id'] = playlist['uri']

                # Splits the playlist title into date and name for data entry
                components = playlist['name'].split(" ",1)
                key_data['name'] = components[1]
                key_data['date'] = components[0]

                key_data['length'] = 0
                key_data['tracks'] = []

                for track in (sp.playlist_tracks(playlist['uri']))['items']:
                    # Adds each song's length to total length of playlist (in ms)
                    key_data['length'] += track['track']['duration_ms']
                    # Adds all track titles to a list associated with that playlist
                    key_data['tracks'].append(track['track']['name'])

                    # Pulls data from each individual track for use in tracks table
                    track_data = {}
                    track_data['track_id'] = track['track']['id']
                    track_data['name'] = track['track']['name']
                    track_data['artist'] = []

                    # Accounts for songs with multiple artists
                    for i in range(len(track['track']['artists'])):
                        track_data['artist'].append(track['track']['artists'][i]['name'])

                        # Adds each artist from each track for use in artists table
                        artist = track['track']['artists'][i]['name']
                        all_artists.append(artist)

                    # Converts artist list (if exists) to a single string
                    track_data['artist'] = ", ".join(track_data['artist'])
                    track_data['count'] = 1

                    all_tracks.append(track_data)

                # Converts playlist length from ms to minutes:seconds for display
                key_data['length'] = key_data['length'] / 60000
                minutes = str(int((key_data['length'] - key_data['length'] % 1)))
                seconds = int((key_data['length'] % 1) * 60)

                if seconds > 9:
                    seconds = str(seconds)
                else:
                    seconds = "0" + str(seconds)

                key_data['length'] = minutes + ":" + seconds

                key_data['tracks'] = ", ".join(key_data['tracks'])

                spin_playlists.append(key_data)
        offset += 50

    # Creates a counter for tracks to determine number of occurrences across all playlists
    count = collections.Counter(item['track_id'] for item in all_tracks)
    for id in count.keys():
        for track in all_tracks:
            if track['track_id'] == id:
                track['count'] = count[id]
            elif track['track_id'] == None:
                track['track_id'] = track['name']

    # Accounts for duplicates by reducing each track to one entry with accurate count
    counted_tracks = []
    for track in all_tracks:
        if track not in counted_tracks:
            counted_tracks.append(track)

    # Creates a counter for artists to determine number of occurrences across all playlists
    artist_obj = collections.Counter(all_artists)

    artist_list = list(dict(artist_obj).keys())
    artist_count = list(dict(artist_obj).values())


    # Each dictionary is inserted into the appropriate table
    for item in spin_playlists:
        cursor.execute("INSERT INTO playlists (name, date, spotify_id, tracks, length) VALUES (?,?,?,?,?)", (item['name'], item['date'], item['spotify_id'], item['tracks'], item['length']))

    for item in counted_tracks:
        cursor.execute("INSERT INTO tracks (track_id, name, artist, count) VALUES (?,?,?,?)", (item['track_id'], item['name'], item['artist'], item['count']))

    for artist, count in zip(artist_list, artist_count):
        cursor.execute("INSERT INTO artists (name, count) VALUES (?,?)", (artist, count))

    # Changes are committed to database
    sqliteConnection.commit()

    # Redirects to homepage
    return redirect("/home")

@app.route('/home')
def home():

    ten_recent = []
    top10_artists = []

    # Pulls 10 most recent playlists used from database for display
    cursor.execute("SELECT name, date, length FROM playlists LIMIT 10")
    playlists_contents = cursor.fetchall()

    for row in playlists_contents:
        current = {}
        current['name'] = row[0]
        current['date'] = row[1]
        current['length'] = row[2]

        ten_recent.append(current)
    
    # Pulls 10 most commonly used artists from database for display
    cursor.execute("SELECT name, count FROM artists ORDER BY count DESC LIMIT 10")
    artist_contents = cursor.fetchall()

    for row in artist_contents:
        current = {}
        current['name'] = row[0]
        current['count'] = row[1]

        top10_artists.append(current)

    return render_template("home.html", ten_recent=ten_recent, top10_artists=top10_artists)

@app.route('/playlists')
def playlists():
    
    # Pulls all playlists from database for display
    cursor.execute("SELECT name, date, tracks, length FROM playlists")
    contents = cursor.fetchall()

    all_playlists = []

    for row in contents:
        current = {}
        current['name'] = row[0]
        current['date'] = row[1]
        current['tracks'] = row[2]
        current['length'] = row[3]

        all_playlists.append(current)
    
    return render_template("playlists.html", all_playlists=all_playlists)

@app.route('/tracks')
def tracks():

    all_tracks = []

    #Pulls all tracks from database for display
    cursor.execute("SELECT name, artist, count FROM tracks ORDER BY count DESC, artist")
    contents = cursor.fetchall()

    for row in contents:
        current = {}
        current['name'] = row[0]
        current['artist'] = row[1]
        current['count'] = row[2]

        all_tracks.append(current)

    return render_template("tracks.html", all_tracks=all_tracks)