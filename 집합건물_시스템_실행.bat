@echo off
chcp 65001 > nul
title 집합건물 분쟁조정위원회 업무시스템

echo.
echo  ================================================
echo   경기도 집합건물 분쟁조정위원회 업무시스템
echo  ================================================
echo.
echo  서버를 시작합니다. 잠시 기다려주세요...
echo.

cd /d "c:\Users\USER\Desktop\클로드코드\집합건물분쟁조정위원회 업무 자동화"

:: 이미 실행 중인 Streamlit 종료
taskkill /f /im streamlit.exe > nul 2>&1
timeout /t 1 > nul

:: 브라우저 자동 열기 (3초 후)
start "" cmd /c "timeout /t 3 > nul && start http://localhost:8501"

:: Streamlit 실행
"C:\Users\USER\AppData\Local\Programs\Python\Python314\Scripts\streamlit.exe" run app.py --server.port 8501 --server.headless true --browser.gatherUsageStats false

pause
