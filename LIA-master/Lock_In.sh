#!/bin/bash

ziDataServer &
startWebServer &
python3 WhiteLight.py &

while pgrep -f "python3 WhiteLight.py" &>/dev/null; do
    sleep 10s
done

kill $( pgrep ziDataServer )
kill $( pgrep ziWebServer )
kill $( pgrep startWebServer )

