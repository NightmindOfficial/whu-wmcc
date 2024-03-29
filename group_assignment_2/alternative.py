import streamlit as st
import spotipy
from spotipy.oauth2 import SpotifyClientCredentials
import pandas as pd
import numpy as np

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

            with tab1:

                info1, features1 = get_playlist_info(url1)
                info2, features2 = get_playlist_info(url2)



                with st.expander("General Information", expanded=True):
                    gen_info_df = pd.DataFrame([info1, info2], index=['Playlist 1', 'Playlist 2']).T
                    st.table(gen_info_df)
                
                # Visualization of aggregated audio features
                with st.expander("Aggregated Audio Features", expanded=True):
                    features_df = pd.DataFrame([features1, features2], index=['Playlist 1', 'Playlist 2'])
                    st.bar_chart(features_df.T)
                
                # Offering more insights (optional)
                    st.markdown("### Additional Insights")
                    st.markdown("Explore how each playlist stands out:")
                    col1, col2 = st.columns(2)
                    with col1:
                        st.metric("More Danceable", "Playlist 1" if features1['danceability'] > features2['danceability'] else "Playlist 2")
                    with col2:
                        st.metric("More Energetic", "Playlist 1" if features1['energy'] > features2['energy'] else "Playlist 2")
                
                # Consider including more comparisons or insights based on other audio features


            with tab2:
                st.info("Empty.")
                # Add Track By Track here

    except Exception as e:
        st.error(f"Analysis failed: {e}. Please make sure the playlist URLs are valid.")
else:
    st.error("Please enter valid URLs for both playlists.")

