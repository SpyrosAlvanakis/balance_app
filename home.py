import streamlit as st 

# Set wide mode
st.set_page_config(layout="wide")

pages=[
       st.Page("pages/interaction.py", title="Interaction"),
       st.Page("pages/plots.py", title="Visualisation"),
       st.Page("pages/predict.py", title="Predict Month")
]
pg = st.navigation(pages)
pg.run()
