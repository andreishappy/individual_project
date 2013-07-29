pids=`ps -elf | grep python  | grep -v grep | grep -v emacs | awk '{print $4}'`
kill -9 $pids
