@echo off
wt -d . cmd /k ".venv\Scripts\activate.bat && uvicorn api.index:app --reload --host 0.0.0.0 --port 8000" ^
; sp -d . cmd /k "npm run dev -- --host 0.0.0.0"