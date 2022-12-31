#!/usr/bin/env bash

PROG="nc"
PROG_ARGS="localhost 30003"
PROG_FILE="/home/pi/flightData.txt"
ALT_FILE="/home/pi/flightData_alt.txt" ## When script is reset at midnight to save space (for 24/7 data collection)
PUSH_DATA = "/home/pi/Flight-Tracker/pushToDB.py"
PIDFILE="/var/run/netcatTransferData.pid"

start() {
      if [ -e $PIDFILE ]; then
          ## Program is running, exit with error.
          echo "Error! $PROG is currently running!" 1>&2
          exit 1
      else
          cd ~
          ## At the end of every data collection, $PROG_FILE will be left for scanning. Therefore, ALT_FILE must be created under all circumstances.
          echo "Creating file" 1>&2
          touch $ALT_FILE
          $PROG $PROG_ARGS >> "${ALT_FILE}" &
          echo "$PROG started" 1>&2
          touch $PIDFILE
      fi
}

stop() {
      if [ -e $PIDFILE ]; then
         ## Program is running, so stop it
         echo "$PROG is running" 1>&2
         killall $PROG
         rm -f $PROG_FILE ## file from previous data collection
         mv $ALT_FILE $PROG_FILE

         rm -f $PIDFILE
         echo "$PROG stopped" 1>&2
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
          sudo python3 $PUSH_DATA
          start
          exit 0
      ;;
      **)
          # none or invalid input -> indicate usage
          echo "Usage: $0 {start|stop|reload}" 1>&2
          exit 1
      ;;
esac
exit 0
