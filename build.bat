@echo off
chcp 65001 >nul
echo ========================================
echo    Сборка Secretary Assistant (Nuitka)
echo ========================================

python -m nuitka ^
  --standalone ^
  --include-data-dir=data=data ^
  --include-data-dir=templates=templates ^
  --include-data-file=icon.ico=icon.ico ^
  --windows-icon-from-ico=icon.ico ^
  --windows-console-mode=disable ^
  --product-name="Secretary Assistant" ^
  --file-description="Secretary Assistant" ^
  --product-version=4.0.0.0 ^
  --file-version=4.0.0.0 ^
  --output-dir=build ^
  --show-progress ^
  --plugin-enable=tk-inter ^
  --include-package=customtkinter ^
  --include-package=openpyxl ^
  main.py

echo.
echo ========================================
echo    Сборка завершена!
echo    Готовая папка: build\main.dist
echo    Запускать: build\main.dist\main.exe
echo ========================================
pause