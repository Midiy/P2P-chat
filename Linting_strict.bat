@echo off
for /f "delims=" %%a in ('dir /a-d /b /s ".\*.py"') do ( 
    flake8 --ignore=E252 "%%a"
    @echo.
)
pause