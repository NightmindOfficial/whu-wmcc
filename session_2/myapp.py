import streamlit as st

# Set the title of the app
st.title('Hello, Otis!')

# Display a simple text
st.write('This is a simple Streamlit app."')


import streamlit as st

# Function to display email in red
def display_email_in_red(email):
    # Using Markdown to render the email in red
    st.markdown(f'<p style="color:red;">{email}</p>', unsafe_allow_html=True)

# Initialize a key in the session state to track button click
if 'button_clicked' not in st.session_state:
    st.session_state.button_clicked = False

# Create a form for the user input
with st.form(key='my_form'):
    name = st.text_input(label='Name')
    email = st.text_input(label='Email Address')
    submit_button = st.form_submit_button(label='Submit')

# Check if the button has been clicked
if submit_button:
    # Update the session state to reflect the button click
    st.session_state.button_clicked = True

# If the button was clicked, display the email in red
if st.session_state.button_clicked:
    display_email_in_red(email)


import matplotlib.pyplot as plt
import numpy as np

# Generating sample data
np.random.seed(0)
x = np.random.rand(50)
y = np.random.rand(50)
colors = np.random.rand(50)
area = (30 * np.random.rand(50))**2  # Circle area

# Creating scatter plot
plt.figure(figsize=(8, 6))
plt.scatter(x, y, s=area, c=colors, alpha=0.5)
plt.title('Sample Scatter Plot')
plt.xlabel('X axis')
plt.ylabel('Y axis')
plt.show()

