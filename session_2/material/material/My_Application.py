import streamlit as st
import pandas as pd
import cv2
import numpy as np

def clicked(b):
	st.write(b)
st.session_state["shared"]=""

st.sidebar.markdown("Hello World")
st.sidebar.markdown("Welcome")
st.sidebar.markdown("Saturday")

st.title("Application")
st.write("Enter your date of birth")
st.latex(r''' \frac{x}{x^2}''')

st.code('for i=1 to 100 do sleep(300)')

st.number_input("Daten",0,100,30,5)
slide_input = st.slider("Pick a number",0,50)

test_button = st.button("Click me")
if test_button:
	clicked(slide_input)	
    
def clicked(msg):
    st.write(msg)
    st.session_state["shared"]=msg
    

col1, col2, col3 = st.columns(3)

with col1:
    st.write("Column 1")
with col2:
    st.number_input("Zahl", 0,10,5,1)
    

    
df = pd.read_csv("melb_data_housing.csv");

st.dataframe(df)

image_file = st.file_uploader("File Uploaed", type="jpg")
if image_file is not None:
    file_bytes = np.asarray(bytearray(image_file.read()), dtype=np.uint8)
    opencv_image = cv2.imdecode(file_bytes, 1)
    st.image(opencv_image, channels="BGR")
    
