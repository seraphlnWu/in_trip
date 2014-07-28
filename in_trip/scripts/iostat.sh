ps -A | grep iostat | grep -P '(\d{3,7})' -o | kill; iostat -x -d 5 >> /tmp/$(date +%Y%m%d).log
