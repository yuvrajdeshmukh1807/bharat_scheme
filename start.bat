@echo off
echo ===================================================
echo     Starting BharatScheme AI (Standalone Mode)
echo ===================================================
echo.
echo Starting React Vite Frontend on http://localhost:5173 ...
echo (Running in Standalone Mode: No backend or database required)
echo.
start "BharatScheme AI Frontend" cmd /k "cd frontend && npm.cmd run dev"

echo ===================================================
echo BharatScheme AI is running!
echo Access the web portal at: http://localhost:5173
echo ===================================================
