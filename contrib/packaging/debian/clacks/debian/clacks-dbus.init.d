#!/bin/sh
### BEGIN INIT INFO
# Provides:          clacks-dbus
# X-Start-Before:    x-display-manager
# X-Interactive:     true
# Required-Start:    $local_fs $network $remote_fs
# Required-Stop:     $local_fs $network $remote_fs
# Should-Start:	     $syslog
# Should-Stop:       $syslog
# Default-Start:     2 3 4 5
# Default-Stop:      0 1 6
# Short-Description: clacks-dbus helper
# Description:       TODO
### END INIT INFO

set -e

PATH=/sbin:/bin:/usr/sbin:/usr/bin
DESC="clacks infrastructure"
SERVICE=dbus
SCRIPTNAME=/etc/init.d/clacks-$SERVICE
FORCE_JOIN=0


start_service() {
        [ -x /usr/sbin/clacks-$SERVICE ] || continue
        PIDFILE=/var/run/clacks/$SERVICE.pid
        PID=$(pgrep clacks-$SERVICE)

        if [ "x$PID" = "x$(cat $PIDFILE)" ]; then
            log_progress_msg "already running"
	else
            start-stop-daemon --background --start --quiet -m --pidfile $PIDFILE \
                --exec /usr/sbin/clacks-$SERVICE
	fi
}


stop_service() {
       [ -x /usr/sbin/clacks-$SERVICE ] || continue
       PIDFILE=/var/run/clacks/$SERVICE.pid
       start-stop-daemon --stop --quiet --oknodo --pidfile $PIDFILE
}


# Gracefully exit if the package has been removed.
test -x /usr/sbin/clacks-$SERVICE || exit 0

. /lib/lsb/init-functions

# Include clacks defaults if available.
test -f /etc/default/$SERVICE && . /etc/default/$SERVICE

if [ ! -d /var/run/clacks ]; then
    install -d -o root -g clacks -m 0770 /var/run/clacks
fi

# Don't start if we're not configured to start
test $FORCE_JOIN = 0 -a ! -e /etc/clacks/config && exit 0

case "$1" in
    start)
        log_daemon_msg "Starting $DESC"
        log_progress_msg "$SERVICE"
        start_service
        log_end_msg $?
        ;;

    stop)
        log_daemon_msg "Stopping $DESC"
        stop_service
        log_progress_msg "$SERVICE"
        log_end_msg $?
        ;;

    restart|force-reload)
        log_daemon_msg "Restarting $DESC"
        log_progress_msg "$SERVICE"
        stop_services
        start_services
        log_end_msg $?
        ;;

    *)
        echo "Usage: $SCRIPTNAME {start|stop|restart|force-reload}" >&2
        exit 1
        ;;
esac

exit 0
