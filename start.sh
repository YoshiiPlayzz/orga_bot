#!/bin/bash 
echo "Der Bot wird abgeglichen mit dem Remote-Branch und wird falls Änderungen diese herunterladen..."
git reset --hard
git pull
chmod 777 start.sh

echo "Der Bot wird nun gestartet!"
screen -S "Orga Bot" python main.py