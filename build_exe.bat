@echo off
setlocal
REM ============================================================
REM  Cartoon AI - one-click build.  Double-click this file on a
REM  Windows 10/11 PC.  Output:  dist\Cartoon.exe  (single file)
REM  Needs: Python 3.10-3.12 (64-bit) from python.org, internet.
REM ============================================================
cd /d "%~dp0"
where py >nul 2>nul && (set PY=py -3) || (set PY=python)
%PY% --version || (echo Python is not installed. Get it from https://www.python.org/downloads/ ^(tick "Add to PATH"^) & pause & exit /b 1)

echo [1/4] Creating build environment...
%PY% -m venv .venv || goto :fail
call .venv\Scripts\activate.bat
python -m pip install --upgrade pip -q || goto :fail
echo [2/4] Installing dependencies (a few minutes the first time)...
pip install -r requirements.txt -q || goto :fail
echo [3/4] Building Cartoon.exe ...
pyinstaller --noconfirm --clean Cartoon.spec || goto :fail
echo [4/4] Testing the built EXE (starts it, opens every screen, closes it)...
set CARTOON_SELFTEST=1
dist\Cartoon.exe > selftest.log 2>&1
findstr /C:"SELFTEST OK" selftest.log >nul || (echo SELF-TEST FAILED - see selftest.log & type selftest.log & pause & exit /b 1)
echo.
echo SUCCESS:  %cd%\dist\Cartoon.exe
explorer dist
pause
exit /b 0
:fail
echo BUILD FAILED. Scroll up for the error.
pause
exit /b 1
