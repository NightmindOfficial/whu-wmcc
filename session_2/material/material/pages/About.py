import streamlit as st

st.set_page_config(page_title="About the app", page_icon=None, layout="centered", initial_sidebar_state="auto", menu_items=None)

st.write("From My App")
st.write(st.session_state["shared"])