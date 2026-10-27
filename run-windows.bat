@echo off
echo Installing requirements...
pip install -r requirements.txt
echo.
echo Open http://localhost:8000 in your browser (ffmpeg must be installed)
python app.py
pause
