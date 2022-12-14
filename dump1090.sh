#!/usr/bin/env bash
PROG="dump1090"
PROG_PATH="/home/pi/dump1090"
PROG_ARGS="--interactive --net --net-sbs-port 30003"
PIDFILE="/var/run/dump1090.pid"

start() {
      cd ~
      if [ -e $PIDFILE ]; then
          ## Program is running, exit with error.
          echo "Error! $PROG is currently running!" 1>&2
          exit 1
      else
          ## Gets rid of output that is not needed
          cd $PROG_PATH
          ./$PROG $PROG_ARGS 2>&1 >/dev/null &
          echo "$PROG started"
          touch $PIDFILE
      fi
}

stop() {
      cd ~
      if [ -e $PIDFILE ]; then
          ## Program is running, so stop it
         echo "$PROG is running"
         killall $PROG
         rm -f $PIDFILE
         echo "$PROG stopped"
      else
          ## Program is not running, exit with error.
          echo "Error! $PROG not started!" 1>&2
          exit 1
      fi
}

## Check to see if we are running as root first.
if [ "$(id -u)" != "0" ]; then
      echo "This script must be run as root" 1>&2
      exit 1
fi

case "$1" in
      start)
          start
          exit 0
      ;;
      stop)
          stop
          exit 0
      ;;
      reload|restart|force-reload)
          stop
          start
          exit 0
      ;;
      **)
          echo "Usage: $0 {start|stop|reload}" 1>&2
          exit 1
      ;;
esac
exit 0
