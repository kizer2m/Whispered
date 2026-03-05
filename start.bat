@echo off
chcp 65001 >nul
title Whispered - Video Transcription
cd /d "%~dp0"
python whispered.py
pause
