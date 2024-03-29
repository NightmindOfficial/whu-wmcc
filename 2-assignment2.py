# Import all necessary packages
import streamlit as st # Application Interfaces
import spotipy # Spotify API Connection
from spotipy.oauth2 import SpotifyClientCredentials # Also Spotify
import pandas as pd # DataFrames
import plotly.graph_objects as go # For plotting graphs
import plotly.express as px # For plotting charts and graphs
from math import pi
import numpy as np

# Use the entire width of the screen for the comparison
st.set_page_config(layout="wide")

# Initialize the Spotipy client with your Spotify API credentials
client_id = 'b7e3715f645d480b93687e744c4287ab'
client_secret = '0bb4c5c2bfef4248933cbf03478756ae'
client_credentials_manager = SpotifyClientCredentials(client_id=client_id, client_secret=client_secret)
sp = spotipy.Spotify(client_credentials_manager=client_credentials_manager)



def get_playlist_by_url(url):
    """Fetch the Spotify playlist object based on what the user put in as the URL"""
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

    # Return a dictionary with the playlist's most basic attributes found in the playlist object
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

    # Get all song IDs, which are later used to determine how many songs there are
    song_ids = [songs[i]['track']['id'] for i in range(0, len(songs))]

    # Batch Extract the Features and store them in a dict with their respective track id
    features = {}
    for i in range(0, len(song_ids), 50):

        audio_features = sp.audio_features(song_ids[i:i+50])

        for feature_set in audio_features:
            if feature_set is not None:
                features[str(feature_set['id'])] = feature_set # Store the features of a track in a dict with key = track id and value = dict of all the features


    # The list song_details will hold all tracks with all info that is available for it, so both general information AND audio features
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
        
        # Combine the track details with its audio features (excluding redundant 'id' and 'duration')
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
        
        # Add the song information to the overall list
        song_details.append(song_info)
    
    # Convert the list into a pandas dataframe to allow later manipulation/filtering etc.
    df = pd.DataFrame(song_details)

    
    return df



# Define demo playlist URLs, that will be used should the user enter no URLs.
demo_url1 = 'https://open.spotify.com/playlist/2rzYlHEy9357Sk9nkTa1qF?si=bf699dbed4514de8'
demo_url2 = 'https://open.spotify.com/playlist/70DNLsTd3V8jUCbeu2No47?si=edc307738d3f42a9'


### MAIN STREAMLIT APPLICATION
    
def main():
    st.title("Spotify Playlist Comparator")
    st.markdown("Compare the vibe and musical qualities of two Spotify playlists.")

    # the Sidebar is used for user input and general information
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

    # Only execute the comparison as soon as the compare button is pressed
    if st.sidebar.button("Compare Playlists 🎛️"):
        
        # If both URL fields are empty, use the demo playlists for the comparison
        if not url1 and not url2:
            url1 = demo_url1
            url2 = demo_url2
            st.info("Continuing with Demo Playlists. To compare your own playlists, please provide URLs for them.")

        # If the URL inputs are filled, try to get the playlist object for it from Spotify
        try:
            pl1 = get_playlist_by_url(url1)
            pl2 = get_playlist_by_url(url2)
        
        # If that fails (e.g., when the link is invalid), abort the comparison with an error
        except Exception as e:
            st.error("Failed to retrieve playlists. Are you sure the URLs are valid and the playlists are public?")
            return

        # If it does not fail, continue with calculating the comparisons.
        try:
            with st.spinner("Analyzing Playlists..."):

                # Get the track information for both playlists and add another column 'playlist-no' for later identification
                df1 = get_tracks_info(pl1)
                df1['playlist-no'] = 1
                df2 = get_tracks_info(pl2)
                df2['playlist-no'] = 2

                # Then merge both dataframes by concatenation. Now, the playlist-no acts as an identifier as to which playlist the song belongs to
                merged_df = pd.concat([df1, df2], ignore_index=True)

                # Drop all features which are not relevant for the comparison
                non_features = ['track-id', 'analysis_url', 'track_href', 'type', 'uri', 'duration_ms']
                merged_df.drop(labels=non_features, axis=1, inplace=True)


                # SECTION ONE - GENERAL INFORMATION
                # Display a table which informs the user about general details of each playlist  - the name, the creator, and no of songs in it
                with st.expander("General Information", expanded=True):
                    st.header("General Information ℹ")
                    info_1 = get_playlist_info(pl1)
                    info_2 = get_playlist_info(pl2)
                    gen_info_df = pd.DataFrame([info_1, info_2], index=['Playlist 1', 'Playlist 2']).T
                    st.table(gen_info_df)
                


                # SECTION TWO - COMPARISON OF AUDIO FEATURES
                # Create a radar chart which compares the mean values of each playlist's audio features for a holistic comparison
                with st.expander("Audio Features", expanded=True):
                    st.header("Audio Features 🎧")
                    st.markdown("Each song has different attributes that Spotify quantifies - for example, if a song has a lot of speech in it (e.g. rap music), these songs will have high levels in the 'speechiness' category and low levels in the 'instrumentalness' category. By comparing these attributes, we can get insights into how the musical style differs in the playlists provided.")
                    
                    # Select Attributes for Comparison
                    attributes = ['danceability', 'energy', 'acousticness', 'liveness', 'loudness', 'speechiness', 'instrumentalness', 'valence']
                    # Normalize the 'loudness' column so it fits with the other values ranging from 0 to 1
                    merged_df['loudness'] = merged_df['loudness'].apply(lambda x: (x - (-60)) / (0 - (-60)))
                    #Then calculate the mean values for each attribute by playlist
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

                        # Add the data traces to the radar with its respective name
                        fig.add_trace(go.Scatterpolar(
                            r=values,
                            theta=categories,
                            fill='toself',
                            name= info_1["Title"] if playlist_no == 1 else info_2["Title"] # Determine the playlist name based on its number
                        ))

                    # Fine-tune the layout of the plot to allow for better readability
                    fig.update_layout(
                        polar=dict(
                            radialaxis=dict(
                                visible=True,
                                range=[0, 1]
                            )
                        ),
                        #Adjust the position of the legend to not overlay the data
                        showlegend=True,
                            legend=dict(
                                orientation="h",  # Set legend orientation to horizontal
                                yanchor="bottom",  # Anchor legend at the bottom
                                y=-0.5,  # Position legend below the plot
                                xanchor="center",  # Center the legend horizontally
                                x=0.5  # Position the center of the legend in the middle of the plot horizontally
                        )
                    )

                    col1, col2 = st.columns(2)
                        
                    with col1:
                        # Finally, plot the chart in the Streamlit page
                        st.plotly_chart(fig)
                    

                    # In the column on the right side, add "shortcuts" that directly show which playlist is stronger in each audio feature.
                    # Each title variable compares whether the first or second playlist's mean value is higher and then either takes the name of the first, or the second playlist.
                    with col2:
                        features1 = mean_values.loc[1].to_dict()
                        features2 = mean_values.loc[2].to_dict()
                        st.markdown("### Executive Summary")
                        st.markdown("Explore how each playlist stands out:")
                        col1, col2 = st.columns(2)
                        with col1:
                            danceability_title = info_1['Title'] if features1['danceability'] > features2['danceability'] else info_2['Title']
                            st.metric("More Danceable 💃", danceability_title)
                            speechiness_title = info_1['Title'] if features1['speechiness'] > features2['speechiness'] else info_2['Title']
                            st.metric("More 'Speechy'", speechiness_title)
                            liveness_title = info_1['Title'] if features1['liveness'] > features2['liveness'] else info_2['Title']
                            st.metric("More Live Content", liveness_title)
                            valence_title = info_1['Title'] if features1['valence'] > features2['valence'] else info_2['Title']
                            st.metric("More Valent/Cheerful", valence_title)


                        with col2:
                            energy_title = info_1['Title'] if features1['energy'] > features2['energy'] else info_2['Title']
                            st.metric("More Energetic 🤟🏻", energy_title)
                            acousticness_title = info_1['Title'] if features1['acousticness'] > features2['acousticness'] else info_2['Title']
                            st.metric("More Acoustic", acousticness_title)
                            instrumentalness_title = info_1['Title'] if features1['instrumentalness'] > features2['instrumentalness'] else info_2['Title']
                            st.metric("More Instrumental", instrumentalness_title)
                            loudness_title = info_1['Title'] if features1['loudness'] > features2['loudness'] else info_2['Title']
                            st.metric("More Loudness", loudness_title)


                # SECTION THREE - COMPARING TIME AND SPEED
                # Create Violin Charts which visualise the differences in the distribution of tempo and song length between the playlists
                with st.expander("Time and Speed", expanded=True):
                    st.header("Time and Speed ⏱")
                    st.markdown("Comparing the average tempo and length of the songs in each playlist can be insightful as it provides hints on the genre and overall valence of the playlists.")

                    # Prepare the datasets for the violin plots by filtering out the relevant data
                    tempo_data = merged_df[['playlist-no', 'tempo']]
                    duration_data = merged_df[['playlist-no', 'duration']]

                    # Function to create violin chart (as we will need it twice)
                    def create_violin_chart(df, y, title):
                        fig = go.Figure()
                        
                        # Iterate through the unique playlist numbers to add each as a trace
                        for playlist_no in sorted(df['playlist-no'].unique()):
                            fig.add_trace(go.Violin(y=df[df['playlist-no'] == playlist_no][y],
                                                    name=info_1["Title"] if playlist_no == 1 else info_2["Title"], # Determine the playlist name based on its number
                                                    box_visible=True,
                                                    meanline_visible=True))
                        
                        # Update the layout and axes
                        fig.update_layout(title=title,
                                        yaxis_title=y,
                                        showlegend=False)
                        
                        return fig

                    # Create violin plots for 'tempo' and 'duration_sec'
                    fig_tempo = create_violin_chart(tempo_data, 'tempo', 'Tempo Comparison')
                    fig_duration = create_violin_chart(duration_data, 'duration', 'Duration Comparison')

                    # Finally, plot the charts in the Streamlit app BENEATH each other to allow comparison of the y-axis
                    col1, col2 = st.columns(2)

                    with col1:
                        st.plotly_chart(fig_tempo, use_container_width=True)

                    with col2:
                        st.plotly_chart(fig_duration, use_container_width=True)



                # SECTION 4 - MODES AND VALENCE
                # Compare the share of "happy" and "sad" songs in the playlist to determine the overall mood, and try to show how valence is related to mode.
                with st.expander("Modes and Valence", expanded=True):
                    st.header("Modes and Valence 😌")
                    st.markdown("By comparing the modes and valence values of the playlists, we can make assumptions about how 'happy' or positive the songs of the playlists are, a key determinant of the overall playlist mood.")


                    # Function to map 'key' numeric values to pitches and 'mode' to Major/Minor
                    # to allow for easy readability by humans (0 and 1 are minor and major, respectively)
                    def map_music_attributes(df):
                        mode_mapping = {0: 'Minor', 1: 'Major'}
                        df['mode'] = df['mode'].map(mode_mapping)
                        return df

                    # Apply the mapping to our DataFrame
                    merged_df_mapped = map_music_attributes(merged_df.copy())


                    # Function to create and return a pie chart figure (we need it twice)
                    def create_pie_chart(playlist_no):
                        #Only use the data from the playlist number that is selected
                        filtered_data = merged_df_mapped[merged_df_mapped['playlist-no'] == playlist_no]
                        # Determine the playlist name based on its number
                        pl_name=info_1["Title"] if playlist_no == 1 else info_2["Title"]

                        # Then create a pie chart showing the share of major vs. minor songs in each Playlist
                        fig = px.pie(filtered_data, names='mode', title=f'Mode Distribution for "{pl_name}"')
                        return fig


                    # Generate and display pie charts for each playlist number
                    col1, col2 = st.columns(2)
                        
                    with col1:
                        fig_key = create_pie_chart(1)
                        st.plotly_chart(fig_key)
                    
                    with col2:
                        fig_mode = create_pie_chart(2)
                        st.plotly_chart(fig_mode)

                    # We also want to show that usually, songs written in major lead to a higher average valence. We do this by showing the difference in valence for major vs. minor songs per playlist.
                    st.markdown("Theoretically, the higher the share of major mode songs, the happier the sounds should sound, thus, valence should be higher.")

                    # Calculate the mean valence by mode for each playlist
                    mean_valence = merged_df_mapped.groupby(['playlist-no', 'mode'])['valence'].mean().reset_index()

                    # Create the bar chart
                    fig = px.bar(mean_valence, x='mode', y='valence', color='mode',
                                barmode='group',
                                facet_col='playlist-no', 
                                title='Average Valence by Mode and Playlist',
                                labels={'valence': 'Average Valence', 'mode': 'Mode'},
                                category_orders={'mode': ['Minor', 'Major'], 'playlist-no': [1, 2]},)
                    
                    # Fine-tuning of the bar chart layout
                    fig.update_layout(yaxis_title='Average Valence',
                                    xaxis_title='Mode',
                                    legend_title='Mode',
                                    legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1))

                    # Finally, plot the figure in Streamlit
                    st.plotly_chart(fig)


                # SECTION FIVE - RAW DATA
                # This is just the aggregated song info, in case it is interesting.
                with st.expander("Raw Track Data (for Debugging etc)"):
                    st.header("Raw Track Information 👾")
                    st.dataframe(merged_df)


        # Should anything fail while running the comparison, the exception will be caught and the error code will be output to the user.
        except Exception as e:
            st.error(f"Analysis failed! Error Code: {e}")


# Boilerplate: Automatically call the main function on startup
if __name__ == "__main__":
    main()
