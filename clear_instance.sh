echo $1

# Kill the engines
pids=`ps -elf | grep DSMEngine\ -namespace\ andrei\ -instance\ $1 | grep -v grep | grep -v emacs | awk '{print $4}'`

echo $pids
kill -9 $pids
