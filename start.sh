#!/bin/bash 
echo "Der Bot wird abgeglichen mit dem Remote-Branch und wird falls Änderungen diese herunterladen..."
git pull

echo "\nDer Bot wird nun gestartet!"
screen -S "Orga Bot" python main.py