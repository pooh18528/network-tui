@echo off
REM Network-TUI Launcher for Windows
REM ดับเบิลคลิกไฟล์นี้เพื่อเปิด TUI
setlocal
chcp 65001 >nul 2>&1

echo [ Network-TUI ] กำลังตรวจสอบ dependencies...
pip show textual >nul 2>&1
if errorlevel 1 goto :install
pip show rich >nul 2>&1
if errorlevel 1 goto :install
pip show psutil >nul 2>&1
if errorlevel 1 goto :install
goto :run

:install
echo ติดตั้ง dependencies...
pip install -r "%~dp0requirements.txt"
if errorlevel 1 (
    echo ติดตั้งไม่สำเร็จ ลอง: pip install --upgrade pip แล้วรันใหม่
    pause
    exit /b 1
)

:run
echo.
echo เปิด Network-TUI...
echo กด Q เพื่อออก, R เพื่อสแกนใหม่, ? เพื่อช่วยเหลือ
echo.

python "%~dp0main.py" %*

