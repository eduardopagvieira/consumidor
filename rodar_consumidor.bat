@echo off
chcp 65001 > nul
cd /d "%~dp0"
set PYTHONIOENCODING=utf-8
set CONDA=%USERPROFILE%\miniconda3
set PATH=%CONDA%;%CONDA%\Library\mingw-w64\bin;%CONDA%\Library\usr\bin;%CONDA%\Library\bin;%CONDA%\Scripts;%PATH%
set PY=%CONDA%\python.exe
echo Organizando os zips de 2025 do Consumidor.gov.br. A janela fecha sozinha ao terminar.
(
  "%PY%" -m pip install --quiet pandas
  "%PY%" baixar_consumidor.py --ano 2025
) > log_consumidor.txt 2>&1
echo Pronto. Resultado salvo em log_consumidor.txt
timeout /t 5 > nul
