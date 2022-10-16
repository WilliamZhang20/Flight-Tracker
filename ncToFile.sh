#!/bin/bash

PROG="nc"
PROG_ARGS="localhost 30003"
PROG_FILE="/home/pi/flightData.txt"
PIDFILE="/var/run/netcatTransferData.pid"

start() {
      if [ -e $PIDFILE ]; then
          ## Program is running, exit with error.
          echo "Error! $PROG is currently running!" 1>&2
          exit 1
      else
          cd ~
          if [ -e $PROG_FILE ]; then
              echo "Removing current file to create new one" 1>&2
              rm -f $PROG_FILE # remove previous file and create new
          fi
          touch $PROG_FILE
          $PROG $PROG_ARGS >> "${PROG_FILE}" &
          echo "$PROG started" 1>&2
          touch $PIDFILE
      fi
}

stop() {
      if [ -e $PIDFILE ]; then
         ## Program is running, so stop it
         echo "$PROG is running" 1>&2
         killall $PROG
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
