#! /bin/sh

echo "Start http sources and wsgi app"

python3 -m http.server 8081 &
echo "source 1 pid" $!

python3 -m http.server 8082 &
echo "source 2 pid" $!

python3 -m http.server 8083 &
echo "source 3 pid" $!


python3 app.py &
echo "wsgi app pid" $!
