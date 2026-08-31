@echo off
cd /d "d:\Project\Archimedes\apps\api"
python check_compile.py
echo.
echo ===
echo Now testing import...
python -c "import app.inngest; print('IMPORT SUCCESS: app.inngest imported successfully')"
