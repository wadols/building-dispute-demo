@echo off
title 집합건물 분쟁조정위원회 업무시스템

echo.
echo  ================================================
echo   경기도 집합건물 분쟁조정위원회 업무시스템
echo  ================================================
echo.
echo  서버를 시작합니다. 잠시 기다려주세요...
echo.

:: 이미 실행 중인 Streamlit 종료
taskkill /f /im streamlit.exe > nul 2>&1
timeout /t 1 > nul

:: Streamlit 실행 (브라우저 자동 열기 포함)
"C:\Users\USER\AppData\Local\Programs\Python\Python314\Scripts\streamlit.exe" run app.py --server.port 8501 --browser.gatherUsageStats false

pause
