#!/bin/bash
pyinstaller --onefile --name francos main.py
mv dist/francos .
rm -r build
rmdir dist
