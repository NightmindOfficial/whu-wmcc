import streamlit as st
import spotipy
from spotipy.oauth2 import SpotifyClientCredentials
import pandas as pd
import numpy as np
from pandas.io.formats.style import Styler
import plotly.graph_objs as go
st.set_page_config(layout="wide")


# Initialize the Spotipy client with your Spotify API credentials
client_id = 'b7e3715f645d480b93687e744c4287ab'
client_secret = '0bb4c5c2bfef4248933cbf03478756ae'
client_credentials_manager = SpotifyClientCredentials(client_id=client_id, client_secret=client_secret)
sp = spotipy.Spotify(client_credentials_manager=client_credentials_manager)

def get_playlist_info(playlist_url):
    """Fetch general information and audio features for a Spotify playlist."""
    playlist_id = playlist_url.split("/")[-1].split("?")[0]
    playlist = sp.playlist(playlist_id)
    tracks = get_playlist_tracks(playlist_id)
    track_ids = [track['track']['id'] for track in tracks if track['track']]
    features = get_track_features(track_ids)
    
    # Convert to DataFrame and clean data
    df_features = pd.DataFrame(features)
    # Ensure all values are numeric and handle NaNs
    df_features = df_features.apply(pd.to_numeric, errors='coerce').fillna(0)
    
    info = {
        'Title': playlist['name'],
        'Created By': playlist['owner']['display_name'],
        'Number of Songs': len(tracks)
    }
    
    # 'Created Date' is not directly available from playlist object; consider using 'snapshot_id' as a proxy if needed
    
    return info, df_features.mean()

def get_playlist_tracks(playlist_id):
    """Retrieve tracks from a Spotify playlist."""
    results = sp.playlist_tracks(playlist_id)
    tracks = results['items']
    while results['next']:
        results = sp.next(results)
        tracks.extend(results['items'])
    return tracks

def get_track_features(track_ids):
    """Fetch audio features for a list of Spotify track IDs."""
    features_list = []
    for i in range(0, len(track_ids), 50):
        batch = track_ids[i:i+50]
        features_list += sp.audio_features(batch)
    return features_list

def make_radar_chart(attributes, values1, values2, title1, title2):
    # Initialisiere das Fig-Objekt mit einer spezifischen Größe und Margin-Einstellungen
    fig = go.Figure(layout=go.Layout(
        title='Playlist Comparison',
        polar=dict(
            radialaxis=dict(
                visible=True,
                range=[0, 1]
            )
        ),
        height=600,  # oder eine andere gewünschte Höhe
        width=800,   # oder eine andere gewünschte Breite
        margin=dict(l=30, r=30, t=50, b=30)
    ))

    # Füge die Daten für die erste Playlist hinzu
    fig.add_trace(go.Scatterpolar(
        r=values1,
        theta=attributes,
        fill='toself',
        name=title1
    ))

    # Füge die Daten für die zweite Playlist hinzu
    fig.add_trace(go.Scatterpolar(
        r=values2,
        theta=attributes,
        fill='toself',
        name=title2
    ))

    # Update die Layout-Einstellungen für Titel und Legende
    fig.update_layout(
        title={
            'text': 'Playlist Comparison',
            'y':0.95,
            'x':0.5,
            'xanchor': 'center',
            'yanchor': 'top'
        },
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="center",
            x=0.5
        )
    )

    return fig






# Define demo playlist URLs
demo_url1 = 'https://open.spotify.com/playlist/0r3ZQCQgzkdDhOpYJHc7Fg?si=f2c05b3480454852'
demo_url2 = 'https://open.spotify.com/playlist/0tZqfeSD2VVoe0sbOEVGJ3?si=d38fae9eba3547d9'

# Initialize session state for input fields and a flag for triggering comparison
if 'url1' not in st.session_state:
    st.session_state['url1'] = ''
if 'url2' not in st.session_state:
    st.session_state['url2'] = ''
if 'trigger_compare' not in st.session_state:
    st.session_state['trigger_compare'] = False




# Streamlit app layout
st.title("Spotify Playlist Comparator")
st.markdown("Compare the vibe and musical qualities of two Spotify playlists.")

col1, col2 = st.columns(2)
with col1:
    url1 = st.text_input(
    "Playlist 1 🎶",
    placeholder = "Paste your first Spotify playlist URL here"
    )
with col2:
    url2 = st.text_input(
    "Playlist 2 🎶",
    placeholder = "Paste your second Spotify playlist URL here"
    )

if st.button("Compare Playlists 🎛️"):
    if not (url1 and url2):
        url1 = demo_url1
        url2 = demo_url2
        st.info("Continuing with Demo Playlists. To compare your own playlists, please provide URLs above.")

    try:
        with st.spinner("Analyzing Playlists..."):

            tab1, tab2 = st.tabs(["Playlist Comparison", "Track-by-Track Analysis"])

            with tab1:#Playlist Comparison

                info1, features1 = get_playlist_info(url1)
                info2, features2 = get_playlist_info(url2)

                with st.expander("General Information", expanded=True):
                    gen_info_df = pd.DataFrame([info1, info2], index=['Playlist 1', 'Playlist 2']).T
                    st.table(gen_info_df)

                
                # Visualization of aggregated audio features
                with st.expander("Aggregated Audio Features", expanded=True):
                    features_df = pd.DataFrame([features1, features2], index=[info1['Title'], info2['Title']])
                    st.bar_chart(features_df.T)
                    attributes = ['acousticness', 'danceability', 'energy', 'instrumentalness', 'liveness', 'loudness', 'speechiness', 'valence']
                    max_loudness = 0  # Setzen Sie hier den maximalen Loudness-Wert, den Sie erwarten.
                    values1 = [features1[attr] for attr in attributes]
                    values2 = [features2[attr] for attr in attributes]

                    # Erstellen Sie das Radar-Chart für den Vergleich beider Playlists
                    radar_chart = make_radar_chart(attributes, values1, values2, info1['Title'], info2['Title'])

                    # Anzeigen des Radar-Charts in Streamlit
                    st.plotly_chart(radar_chart, use_container_width=False)
                
                # Offering more insights (optional)
                    st.markdown("### Additional Insights")
                    st.markdown("Explore how each playlist stands out:")
                    col1, col2 = st.columns(2)
                    with col1:
                        danceability_title = info1['Title'] if features1['danceability'] > features2['danceability'] else info2['Title']
                        st.metric("More Danceable", danceability_title)
                    with col2:
                        energy_title = info1['Title'] if features1['energy'] > features2['energy'] else info2['Title']
                        st.metric("More Energetic", energy_title)
                
                # Consider including more comparisons or insights based on other audio features


            with tab2: #Track-by-Track Analysis
                st.info("Empty.")
                # Add Track By Track here

    except Exception as e:
        st.error(f"Analysis failed: {e}. Please make sure the playlist URLs are valid.")
else:
    st.error("Please enter valid URLs for both playlists.")

