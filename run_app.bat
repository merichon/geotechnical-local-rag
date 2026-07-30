@echo off
title Geoteknik Asistan
cd /d "C:\Users\Merich\Claude\Projects\local llm deneme"

echo ============================================================
echo   GEOTEKNIK ASISTAN baslatiliyor...
echo ============================================================
echo.
echo [1/3] Foundry Local servisi baslatiliyor...
foundry server start

echo.
echo [2/3] Model yukleniyor (phi-4-mini)...
foundry model load phi-4-mini

echo.
echo [3/3] Arayuz aciliyor. Tarayicida http://localhost:8501 acilacak.
echo Kapatmak icin bu pencereyi kapatin.
echo.
venv\Scripts\python.exe -m streamlit run app.py --server.fileWatcherType none

pause
