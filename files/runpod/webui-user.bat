@echo off

set PYTHON=
set GIT=
set VENV_DIR=
set COMMANDLINE_ARGS=--opt-sdp-attention --opt-split-attention --enable-insecure-extension-access --share --no-half-vae --no-half --precision full --skip-install --listen

call webui.bat
