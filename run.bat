@echo off
echo Starting AI Safety Analyzer MVP...

echo Installing Frontend Modules if missing...
cd frontend
call npm install
cd ..

echo Starting Django Backend...
start cmd /k "venv\Scripts\activate.bat && python manage.py runserver"

echo Starting Django-Q Background Worker...
start cmd /k "venv\Scripts\activate.bat && python manage.py qcluster"

echo Starting React Frontend...
cd frontend
start cmd /k "npm run dev"

echo All services deploying locally!
echo Backend API : http://localhost:8000
echo Frontend UI : http://localhost:5173
pause
