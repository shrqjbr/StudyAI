import streamlit as st

st.title("🧠 StudyAI")
st.write("Welcome to StudyAI!")

name = st.text_input("What's your name?")

if name:
    st.write("Hello", name + "!")