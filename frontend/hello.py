import streamlit as st

st.write('Hello world')
x = st.text_input('Favorite Movie?')
st.write(f"Your favorite movie is: {x}")