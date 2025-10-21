# Kernel Debug — CV Reviewer

A simple Streamlit app to:

- Score the CV with lightweight heuristics
- Suggest matching jobs based on detected skills

## Requirements

Python 3.12+

Dependencies (managed via `pyproject.toml`):

- streamlit
- google-adk (for the agent definition used by the backend code)
- FastAPI

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

    for linux

   ```
   source .venv/bin/activate
   ```

4. Install dependencies:

    ```pwsh
    uv sync
    ```

5. Run ADK as a web server

    ```pwsh
    adk api_server
    ```

6. Run the Streamlit UI:

    ```pwsh
    streamlit run main.py
    ```

Then open the local URL shown by Streamlit (typically <http://localhost:8501>), upload a PDF CV, and review the results.


## Docker

1. **Pull the Docker image**

    Run the following command to pull the latest Docker image:

    ```bash
    docker pull dzuladj/cv-reviewer:ui-latest
    ```

    and

   ```bash
   docker pull dzuladj/cv-reviewer:adk-latest
   ```

2. **Create Docker Network for UI and ADK**

   Run the following command:

   ```bash
   docker network create your_custom_network
   ```

3. **Run Docker image**

   ADK image:
   
    ```bash
   docker run -d --name your_adk_container_name --network your_custom_network -p 8000:8000 dzuladj/cv-reviewer:adk-latest
   ```

   Streamlit (UI):
    
   ```bash
   docker run -d --name your_ui_container_name --network your_custom_network -p 8501:8501 -e ADK_SERVER=http://your_adk_container_name:8000 dzuladj/cv-reviewer:ui-latest
   ```

The People Behind the Project 👥
- Derajat Salim Wibowo
- Yusuf Martinus Arief
- Dzulfikri Adjmal
