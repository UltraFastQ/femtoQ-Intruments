#!/bin/bash

ziDataServer &
startWebServer &
./dist/Main_Frame/Main_Frame&

while pgrep "Main_Frame" &>/dev/null; do
    sleep 10s
done

kill $( pgrep ziDataServer )
kill $( pgrep ziWebServer )
kill $( pgrep startWebServer )

