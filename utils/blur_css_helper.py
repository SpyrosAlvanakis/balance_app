import streamlit as st

def apply_blur_css():
    # Apply CSS for stronger blurring
    st.markdown("""
    <style>
    /* Blur Plotly charts and other visualizations */
    .js-plotly-plot, .plotly, .plot-container, .user-select-none,
    .svg-container, .main-svg, .js-plotly-plot .plot-container {
        filter: blur(8px) !important;
        pointer-events: none !important;
    }
    
    /* Blur any dataframes */
    .stDataFrame, .stTable {
        filter: blur(8px) !important;
        pointer-events: none !important;
    }
    
    /* Ensure all table contents are blurred */
    [data-testid="StyledDataFrameDataCell"],
    [data-testid="StyledDataFrameHeaderCell"] {
        filter: blur(6px) !important;
    }
    </style>
    """, unsafe_allow_html=True)