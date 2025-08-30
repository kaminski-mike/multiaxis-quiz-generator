@echo off
echo Building Multiaxis Intelligence - Quiz Generator executable MultiaxisQuizGenerator.exe...

echo Building Multiaxis Quiz Generator executable...
pyinstaller --onefile --windowed --icon="../assets/Multiaxis Quiz Generator.ico" ^
--add-data "../assets/*;assets/" ^
--hidden-import tkinter ^
--exclude-module PyQt5 ^
--exclude-module matplotlib ^
--exclude-module numpy ^
--exclude-module pandas ^
--clean --noupx MultiaxisQuizGenerator.py

echo Build complete! MultiaxisQuizGenerator.exe created.
pause
