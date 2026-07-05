import os
from dotenv import load_dotenv

load_dotenv()

import streamlit as st

st.write("HOST:", os.getenv("DB_HOST"))
st.write("USER:", os.getenv("DB_USER"))
st.write("DATABASE:", os.getenv("DB_NAME"))
st.write("PASSWORD:", os.getenv("DB_PASSWORD"))
