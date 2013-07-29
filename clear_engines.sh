# Kill the engines
pids=`ps -elf | grep DSMEngine | grep -v grep | grep -v emacs | awk '{print $4}'`
kill -9 $pids

pids=`ps -elf | grep start1engine.py | grep -v grep | grep -v emacs | awk '{print $4}'`
kill -9 $pids

pids=`ps -elf | grep start_simple.py | grep -v grep | grep -v emacs | awk '{print $4}'`
kill -9 $pids
