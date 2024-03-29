import streamlit as st
import spotipy
from spotipy.oauth2 import SpotifyClientCredentials
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from math import pi
import numpy as np

st.set_page_config(layout="wide")

# Initialize the Spotipy client with your Spotify API credentials
client_id = 'b7e3715f645d480b93687e744c4287ab'
client_secret = '0bb4c5c2bfef4248933cbf03478756ae'
client_credentials_manager = SpotifyClientCredentials(client_id=client_id, client_secret=client_secret)
sp = spotipy.Spotify(client_credentials_manager=client_credentials_manager)


def get_playlist_by_url(url):
    playlist_id = url.split("/")[-1].split("?")[0] # Extract only the ID from the URL provided
    playlist = sp.playlist(playlist_id) # Fetch the entire playlist from spotify by its ID. If this fails, the Exception will be caught during the Streamlit runtime.
    return playlist

def get_playlist_info(playlist):
    """Fetch general information for a Spotify playlist."""

    tracks = playlist["tracks"]
    songs = tracks['items']
    while tracks['next']:
        tracks = sp.next(tracks)
        [songs.append(item) for item in tracks['items']]

    info = {
    'Title': playlist['name'],
    'Created By': playlist['owner']['display_name'],
    'Number of Songs': len(songs),
    }

    return info

def get_tracks_info(playlist):
    """Fetch a dataframe for specific track and audio features information for a Spotify playlist."""

    tracks = playlist["tracks"]
    songs = tracks['items']

    while tracks['next']:
        tracks = sp.next(tracks)
        [songs.append(item) for item in tracks['items']]

    song_ids = [songs[i]['track']['id'] for i in range(0, len(songs))]


    features = {}
    for i in range(0, len(song_ids), 50):

        audio_features = sp.audio_features(song_ids[i:i+50])

        for feature_set in audio_features:
            if feature_set is not None:
                features[str(feature_set['id'])] = feature_set

    song_details = []


    # Loop through each song to fetch its details and audio features
    for song in songs:
        track = song['track']
        track_id = track['id']
        title = track['name']
        artist = track['artists'][0]['name']  # Assuming the first artist is the primary
        album = track['album']['name']
        duration = track['duration_ms']
        created_date = track['album']['release_date']  # Release date of the album
        
        # Combine the track details with its audio features (excluding redundant 'id')
        song_info = {
            'track-id': track_id,
            'title': title,
            'artist': artist,
            'album': album,
            'duration' : float(duration),
            'created-date': created_date,
        }
        
        # Add the audio features to the song info, if available
        for key, value in features[track_id].items():
                if key != 'id':  # Avoid duplicating the track ID
                    song_info[key] = value
        
        song_details.append(song_info)
    

    df = pd.DataFrame(song_details)

    
    return df



# Define demo playlist URLs
demo_url1 = 'https://open.spotify.com/playlist/2rzYlHEy9357Sk9nkTa1qF?si=bf699dbed4514de8'
demo_url2 = 'https://open.spotify.com/playlist/70DNLsTd3V8jUCbeu2No47?si=edc307738d3f42a9'


# Streamlit app layout
    
def main():
    st.title("Spotify Playlist Comparator")
    st.markdown("Compare the vibe and musical qualities of two Spotify playlists.")

    st.sidebar.title("Playlist Input")
    url1 = st.sidebar.text_input(
    "Playlist 1 🎶",
    placeholder = "Paste your first Spotify playlist URL here"
    )
    url2 = st.sidebar.text_input(
    "Playlist 2 🎶",
    placeholder = "Paste your second Spotify playlist URL here"
    )
    st.sidebar.info("Note: If no URLs are specified, two exemplary playlists will be used for which we think a comparison is interesting.")

    if st.sidebar.button("Compare Playlists 🎛️"):
        if not url1 and not url2:
            url1 = demo_url1
            url2 = demo_url2
            st.info("Continuing with Demo Playlists. To compare your own playlists, please provide URLs for them.")

        try:
            pl1 = get_playlist_by_url(url1)
            pl2 = get_playlist_by_url(url2)
        
        except Exception as e:
            st.error("Failed to retrieve playlists. Are you sure the URLs are valid and the playlists are public?")
            return

        try:
            with st.spinner("Analyzing Playlists..."):

                df1 = get_tracks_info(pl1)
                df1['playlist-no'] = 1
                df2 = get_tracks_info(pl2)
                df2['playlist-no'] = 2
                merged_df = pd.concat([df1, df2], ignore_index=True)

                non_features = ['track-id', 'analysis_url', 'track_href', 'type', 'uri', 'duration_ms']
                merged_df.drop(labels=non_features, axis=1, inplace=True)



                with st.expander("General Information", expanded=True):
                    st.header("General Information")
                    info_1 = get_playlist_info(pl1)
                    info_2 = get_playlist_info(pl2)
                    gen_info_df = pd.DataFrame([info_1, info_2], index=['Playlist 1', 'Playlist 2']).T
                    st.table(gen_info_df)
                
                # Visualization of aggregated audio features
                with st.expander("Audio Features", expanded=True):
                    st.header("Audio Features")
                    st.markdown("Each song has different attributes that Spotify quantifies - for example, if a song has a lot of speech in it (e.g. rap music), these songs will have high levels in the 'speechiness' category and low levels in the 'instrumentalness' category. By comparing these attributes, we can get insights into how the musical style differs in the playlists provided.")
                    

                    attributes = ['danceability', 'energy', 'acousticness', 'liveness', 'loudness', 'speechiness', 'instrumentalness', 'valence']
                    # Normalize the 'loudness' column so it fits with the other values ranging from 0 to 1
                    merged_df['loudness'] = merged_df['loudness'].apply(lambda x: (x - (-60)) / (0 - (-60)))
                    mean_values = merged_df.groupby('playlist-no')[attributes].mean()
                    # Initialize a figure
                    fig = go.Figure()

                    # Add traces, one for each playlist
                    for playlist_no in mean_values.index:
                        # Prepare data for radar chart
                        # Note: Plotly's radar chart needs data in a circular format, with the start value repeated at the end.
                        categories = mean_values.columns
                        values = mean_values.loc[playlist_no].tolist() + mean_values.loc[playlist_no].tolist()[:1]
                        categories = categories.append(categories[:1])

                        fig.add_trace(go.Scatterpolar(
                            r=values,
                            theta=categories,
                            fill='toself',
                            name= info_1["Title"] if playlist_no == 1 else info_2["Title"]
                        ))

                    # Fine-tune the layout of the plot
                    fig.update_layout(
                        polar=dict(
                            radialaxis=dict(
                                visible=True,
                                range=[0, 1]
                            )
                        ),
                        showlegend=True,
                            legend=dict(
                                orientation="h",  # Set legend orientation to horizontal
                                yanchor="bottom",  # Anchor legend at the bottom
                                y=-0.5,  # Position legend below the plot
                                xanchor="center",  # Center the legend horizontally
                                x=0.5  # Position the center of the legend in the middle of the plot horizontally
                        )
                    )

                    # In a Streamlit app, use st.plotly_chart(fig) to display the chart
                    st.plotly_chart(fig)

                with st.expander("Time and Speed", expanded=True):
                    st.header("Time and Speed")
                    st.markdown("Comparing the average tempo and length of the songs in each playlist can be insightful as it provides hints on the genre and overall valence of the playlists.")




                    # Prepare the datasets for the violin plots
                    tempo_data = merged_df[['playlist-no', 'tempo']]
                    duration_data = merged_df[['playlist-no', 'duration']]


                    # Function to create violin chart
                    def create_violin_chart(df, y, title):
                        fig = go.Figure()
                        
                        # Iterate through the unique playlist numbers to add each as a trace
                        for playlist_no in sorted(df['playlist-no'].unique()):
                            fig.add_trace(go.Violin(y=df[df['playlist-no'] == playlist_no][y],
                                                    name=info_1["Title"] if playlist_no == 1 else info_2["Title"],
                                                    box_visible=True,
                                                    meanline_visible=True))
                        
                        # Update layout
                        fig.update_layout(title=title,
                                        yaxis_title=y,
                                        showlegend=False)
                        
                        return fig

                    # Create violin plots for 'tempo' and 'duration_sec'
                    fig_tempo = create_violin_chart(tempo_data, 'tempo', 'Tempo Comparison')
                    fig_duration = create_violin_chart(duration_data, 'duration', 'Duration Comparison')

                    # To display in Streamlit, use the following commands:

                    col1, col2 = st.columns(2)

                    with col1:
                        st.plotly_chart(fig_tempo, use_container_width=True)

                    with col2:
                        st.plotly_chart(fig_duration, use_container_width=True)




                with st.expander("Modes and Valence", expanded=True):
                    st.header("Modes and Valence")
                    st.markdown("By comparing the modes and valence values of the playlists, we can make assumptions about how 'happy' or positive the songs of the playlists are, a key determinant of the overall playlist mood.")


                    # Function to map 'key' numeric values to pitches and 'mode' to Major/Minor
                    def map_music_attributes(df):
                        mode_mapping = {0: 'Minor', 1: 'Major'}
                        df['mode'] = df['mode'].map(mode_mapping)
                        return df

                    # Apply the mapping to your DataFrame
                    merged_df_mapped = map_music_attributes(merged_df.copy())
                    color_discrete_map = {
                        'Major': '#ef553b',  # Red
                        'Minor': '#636efa'   # Blue
                    }



                    # Function to create and return a pie chart figure
                    def create_pie_chart(playlist_no):
                        filtered_data = merged_df_mapped[merged_df_mapped['playlist-no'] == playlist_no]
                        pl_name=info_1["Title"] if playlist_no == 1 else info_2["Title"]

                        fig = px.pie(filtered_data, names='mode', title=f'Mode Distribution for "{pl_name}"', color_discrete_map=color_discrete_map)
                        return fig


                    # Generate and display pie charts for each playlist number
                    col1, col2 = st.columns(2)
                        
                    with col1:
                        fig_key = create_pie_chart(1)
                        st.plotly_chart(fig_key)
                    
                    with col2:
                        fig_mode = create_pie_chart(2)
                        st.plotly_chart(fig_mode)


                    st.markdown("Theoretically, the higher the share of major mode songs, the happier the sounds should sound, thus, valence should be higher.")

                    # Calculate the mean valence by mode for each playlist
                    mean_valence = merged_df_mapped.groupby(['playlist-no', 'mode'])['valence'].mean().reset_index()

                    # Create the bar chart
                    fig = px.bar(mean_valence, x='mode', y='valence', color='mode',
                                barmode='group',
                                facet_col='playlist-no', 
                                title='Average Valence by Mode and Playlist',
                                labels={'valence': 'Average Valence', 'mode': 'Mode'},
                                category_orders={'mode': ['Minor', 'Major'], 'playlist-no': [1, 2]},
                                color_discrete_map=color_discrete_map)

                    fig.update_layout(yaxis_title='Average Valence',
                                    xaxis_title='',
                                    legend_title='Mode',
                                    legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1))

                    # Display the figure in your Streamlit app
                    st.plotly_chart(fig)



                with st.expander("Raw Track Data (for Debugging etc)"):
                    st.dataframe(merged_df)
                    st.markdown(merged_df.dtypes)



        except Exception as e:
            st.error(f"Analysis failed! Please ensure the playlist URLs are valid. Error Code: {e}")


# Boilerplate: Automatically call the main function on startup
if __name__ == "__main__":
    main()
