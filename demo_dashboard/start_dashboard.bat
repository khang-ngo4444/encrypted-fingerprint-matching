@echo off
title BioCipher - Live Dashboard & FHE Matching Demo
cd /d "%~dp0"
echo =======================================================================
echo          BIOCIPHER - LIVE DASHBOARD & AUTOMATION DEMO
echo =======================================================================
echo Dang khoi dong Web Server tai http://localhost:8080 ...
echo Trinh duyet se tu dong mo trong 2 giay.
echo Nhan Ctrl+C de dung server bat ky luc nao.
echo =======================================================================

start http://localhost:8080
python server.py 8080
pause
