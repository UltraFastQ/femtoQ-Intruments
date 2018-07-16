#!/bin/bash

ziDataServer &
startWebServer &
python3 WhiteLight.py&

while pgrep -f "python3 WhiteLight.py" &>/dev/null; do
    echo "hello World"
    sleep 10s
done

kill $(ps aux | grep ziDataServer | awk '{print $2}')
kill $(ps aux | grep startWebServer | awk '{print $2}')
kill $(ps aux | grep ziWebServer | awk '{print $2}')

