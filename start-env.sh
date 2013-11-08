
if /bin/ps aux | /bin/grep "[e]nv-twitter.py" > /dev/null
then 
    echo "running"
else
    /usr/bin/screen -S env -d -m sudo ./env-twitter.py
fi
