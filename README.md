# PDF Flatpack Streamlit App

[![Streamlit App](https://static.streamlit.io/badges/streamlit_badge_black_white.svg)](https://pdf-flatpack.streamlit.app)

This project helps users to flatten PDFs and access the transformed PDFs via a download button.

# How the App works?
1. Allow user to upload PDF
2. If a PDF is provided:
  * offer an option to flatten the PDF
3. Any transformations done to the PDF should be accessible by the user
via a download button

# How it's [vibe coded](https://simonwillison.net/2025/Mar/19/vibe-coding/)?
1. start the project with uv: `uv init st-pypdf-forge`
2. add requirements with uv: `uv add streamlit pypdf pymupdf pillow`
3. use [zed agent](https://zed.dev/agentic) with Claude Sonnet 4:
  > can you follow the instruction in the readme's "How the App works?" section to build a streamlit app in `streamlit_app.py`?
4. deploy using [Streamlit Cloud](https://share.streamlit.io)
