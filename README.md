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

```pwsh
py -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -U pip
pip install streamlit pymupdf google-adk
```

Run the Streamlit UI:

```pwsh
streamlit run main.py
```

Then open the local URL shown by Streamlit (typically <http://localhost:8501>), upload a PDF CV, and review the results.

Alternatively, you can use the preconfigured VS Code task "Run Streamlit" from the Command Palette or the Run and Debug panel.

## Notes

- For image-only PDFs (scanned CVs), the text extraction may be empty. Consider running OCR beforehand.
- Job recommendations are heuristic and based on simple keyword matches; refine the mapping in `main.py` as needed.

