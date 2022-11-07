#!/bin/bash 
echo "Der Bot wird abgeglichen mit dem Remote-Branch und wird falls Änderungen diese herunterladen..."
git reset --hard
git pull
sudo chmod 777 start.sh
sleep 2

echo "Der Bot wird nun gestartet!"
sleep 1
screen -S "Orga Bot" python main.py