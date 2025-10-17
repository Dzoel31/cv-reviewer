# Kernel Debug — CV Reviewer

A simple Streamlit app to:

- Extract text from PDF CVs using PyMuPDF
- Parse heuristic sections (summary, skills, experience, etc.)
- Score the CV with lightweight heuristics
- Suggest matching jobs based on detected skills

## Requirements

Python 3.12+

Dependencies (managed via `pyproject.toml`):

- pymupdf
- streamlit
- google-adk (for the agent definition used by the backend code)

## Quick start

Create a virtual environment (optional) and install dependencies:

1. Install uv and create a virtual environment:

    ```pwsh
    uv venv --python 3.12
    ```

2. Activate the virtual environment:

    ```pwsh
    .\.venv\Scripts\Activate.ps1
    ```

3. Install dependencies:

    ```pwsh
    uv sync
    ```

4. Run ADK as a web server

    ```pwsh
    adk api_server
    ```

5. Run the Streamlit UI:

    ```pwsh
    streamlit run main.py
    ```

Then open the local URL shown by Streamlit (typically <http://localhost:8501>), upload a PDF CV, and review the results.
