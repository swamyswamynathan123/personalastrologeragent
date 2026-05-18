@echo off

:: Check if venv exists, create and install dependencies if not
if not exist "venv\Scripts\activate.bat" (
    echo [1/3] Creating virtual environment...
    python -m venv venv
    if errorlevel 1 (
        echo ERROR: Failed to create virtual environment. Is Python installed?
        pause
        exit /b 1
    )

    echo [2/3] Installing dependencies...
    call venv\Scripts\activate
    pip install -r requirements.txt
    if errorlevel 1 (
        echo ERROR: Failed to install dependencies.
        pause
        exit /b 1
    )
    echo [3/3] Setup complete. Starting app...
) else (
    call venv\Scripts\activate
)

streamlit run app.py
