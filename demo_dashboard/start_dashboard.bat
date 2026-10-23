@echo off
title BioCipher - Live Dashboard, Hot-Folder Watcher & FHE Demo
cd /d "%~dp0"
echo =======================================================================
echo          BIOCIPHER - LIVE DASHBOARD & HOT-FOLDER WATCHER
echo =======================================================================
echo Dang khoi dong Web Server tai http://localhost:8080 ...
echo [OK] Hot-Folder Watcher: Dang lang nghe thu muc check_folder\
echo [OK] Kho mau van tay san sang: sample_fingerprints_to_paste\
echo Trinh duyet se tu dong mo trong 2 giay.
echo Nhan Ctrl+C de dung server bat ky luc nao.
echo =======================================================================

start http://localhost:8080
python server.py 8080
pause
