# Kill the engines
pids=`ps -elf | grep DSMEngine | grep -v grep | grep -v emacs | awk '{print $4}'`
kill -9 $pids
