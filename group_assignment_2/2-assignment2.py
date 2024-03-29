### Spotify Playlist Comparison Storyteller ###
#
#   Authors: Bachem, Kilian; Mohr, Otis
#   Submission Date: 29.03.2024, 23:59 CEST


### Import necessary packages

import streamlit as st
import spotipy # To make requests to the Spotify API
import spotipy.util as util
from spotipy.oauth2 import SpotifyClientCredentials

import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt



### PART 1: FUNCTIONS ###
#
#   These functions will be used later in the second part for building the content of the Streamlit application.
#   Scroll down to Part 2 for the Streamlit part.
#

# Initialize Spotipy with user credentails. These will be revoked after the assignment has been graded. Nevertheless, please keep this file confidential.
def init_spotipy():
    client = 'b7e3715f645d480b93687e744c4287ab'
    secret = '0bb4c5c2bfef4248933cbf03478756ae'
    
    client_credentials_manager = SpotifyClientCredentials(client_id=client, client_secret=secret)
    sp = spotipy.Spotify(client_credentials_manager=client_credentials_manager)
    return sp

def fetch_playlist_tracks(sp, username, playlist_id):
    playlist = sp.user_playlist(username, playlist_id) # Get the playlist from the URL provided. This function works also with full links, not just the ID.
    tracks = playlist['tracks']
    songs = tracks['items']
    while tracks['next']:
        tracks = sp.next(tracks)
        songs.extend(tracks['items'])
    song_ids = [song['track']['id'] for song in songs if song['track']]
    return song_ids

def get_audio_features(sp, song_ids, class_label):
    features = []
    for i in range(0, len(song_ids), 50):
        audio_features = sp.audio_features(song_ids[i:i + 50])
        for track in audio_features:
            if track:
                track['class'] = class_label
                features.append(track)
    return features


### PART 2: STREAMLIT APPLICATION ###
#
#   In the main part, the Streamlit Application will provide a user interface   
#   for comparing two different Spotify Playlists from user-provided links
#   and then use the functions of Part 1 to create relevant comparisons.
#


def main():
    st.title("Spotify Playlist Features Comparison")

    username = "kilian.bachem"  # You may want to make this configurable through the UI
    sp_api = init_spotipy(); # Initialize the API ONCE on startup and hand it to the functions thereafter (instead of having to initialize them each time in the functions)

    # User inputs for playlist IDs
    playlist1_id = st.text_input(
    "Playlist 1 🎶",
    placeholder = "Paste your first Spotify playlist URL here"
    )
    playlist2_id = st.text_input(
    "Playlist 2 🎶",
    placeholder = "Paste your second Spotify playlist URL here"
    )

    if st.button("Compare 🎛️"):
        # Fetch playlists and features
        playlist1_song_ids = fetch_playlist_tracks(sp_api, username, playlist1_id)
        playlist2_song_ids = fetch_playlist_tracks(sp_api, username, playlist2_id)

        playlist1_features = get_audio_features(sp_api, playlist1_song_ids, class_label=1)
        playlist2_features = get_audio_features(sp_api, playlist2_song_ids, class_label=0)

        # Combine and preprocess data
        features = playlist1_features + playlist2_features
        df = pd.DataFrame(features)
        non_features = ['analysis_url', 'id', 'track_href', 'type', 'uri']
        df.drop(labels=non_features, axis=1, inplace=True)

        # Split by class (playlist) for plotting
        playlist1_features = df[df['class'] == 0]
        playlist2_features = df[df['class'] == 1]

        # Plotting (for simplicity, only plotting acousticness here)
        #fig, ax = plt.subplots()
        #sns.histplot(slayer_df["acousticness"], ax=ax, color="blue", label="Slayer")
        #sns.histplot(reading_df["acousticness"], ax=ax, color="black", label="Reading")
        #st.pyplot(fig)


        fig = plt.figure(dpi=100)
        fig.subplots_adjust(hspace=0.4, wspace=0.4)
        fig.add_subplot(3, 2, 1)
        sns.histplot( playlist1_features["acousticness"])
        fig.add_subplot(3, 2, 2)
        sns.histplot( playlist2_features["acousticness"])

        fig.add_subplot(3, 2, 3)
        sns.histplot( playlist1_features["loudness"])
        fig.add_subplot(3, 2, 4)
        sns.histplot( playlist2_features["loudness"])

        fig.add_subplot(3, 2, 5)
        sns.histplot( playlist1_features["tempo"])
        fig.add_subplot(3, 2, 6)
        sns.histplot( playlist2_features["tempo"])

        st.pyplot(fig)


# Boilerplate: Automatically call the main function on startup
if __name__ == "__main__":
    main()
