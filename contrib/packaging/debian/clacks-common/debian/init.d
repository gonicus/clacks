#!/bin/sh
### BEGIN INIT INFO
# Provides:          clacks-client
# X-Start-Before:    x-display-manager
# X-Interactive:     true
# Required-Start:    $syslog $network
# Required-Stop:
# Should-Start:	     $syslog
# Should-Stop:       $syslog
# Default-Start:     2 3 4 5
# Default-Stop:      0 1 6
# Short-Description: clacks-client service
# Description:       TODO
### END INIT INFO

set -e

PATH=/sbin:/bin:/usr/sbin:/usr/bin
DESC="clacks infrastructure"
SERVICES="agent dbus client"
SCRIPTNAME=/etc/init.d/clacks
FOUND=0
FORCE_JOIN=0


join_required() {
    test $FORCE_JOIN -eq 0 && return 0
    test -e /usr/sbin/clacks-client || return 0

    if [ -e /etc/clacks/config ]; then
        grep -q '^\s*key\s*=\s*..*$' /etc/clacks/config && return 0
    fi

    return 1
}


start_services() {
        STATUS=0
        for SERVICE in $SERVICES; do
            PIDFILE=/var/run/clacks/$SERVICE.pid
            start-stop-daemon --start --quiet --pidfile $PIDFILE \
                --exec /usr/sbin/clacks-$SERVICE -- --pid-file $PIDFILE
            test $? -ne 0 && STATUS=1

            log_progress_msg "$SERVICE"
        done

        return $STATUS
}


stop_services() {
        STATUS=0
        for SERVICE in `echo -n "$SERVICES " | tac -s \ `; do
            PIDFILE=/var/run/clacks/$SERVICE.pid
            start-stop-daemon --stop --quiet --pidfile $PIDFILE
            test $? -ne 0 && STATUS=1

            test $1 -eq 1 && log_progress_msg "$SERVICE"
        done

        return $STATUS
}


# Gracefully exit if the package has been removed.
for SERVICE in $SERVICES; do
	test -x /usr/sbin/clacks-$SERVICE && FOUND=1
done
test $FOUND -eq 0 && exit 0

. /lib/lsb/init-functions

# Include clacks defaults if available.
test -f /etc/default/clacks && . /etc/default/clacks

if [ ! -d /var/run/clacks ]; then
    install -d -o root -g clacks -m 0770 /var/run/clacks
fi

# Don't start if we're not configured to start
test $START_AGENT -eq 0 -a $START_CLIENT -eq 0 && exit 0
test $FORCE_JOIN -eq 0 -a ! -e /etc/clacks/config && exit 0

case "$1" in
    start)
        # If a join is obligatory, stay in this loop until we're
        # joined. This should block the boot process.
        while join_required; do
            log_daemon_msg "Joining to the clacks infrastructure"
            clacks-join
            log_end_msg $?
        done

        # If we've no configuration now, stop more or less silently
        if [ ! -e /etc/clacks/config ]; then
            exit 0
        fi

        log_daemon_msg "Starting $DESC"
        start_services
        log_end_msg $?
        ;;

    stop)
        log_daemon_msg "Stopping $DESC"
        stop_services 1
        log_end_msg $?
        ;;

    restart|force-reload)
        log_daemon_msg "Restarting $DESC"
        stop_services 0 && start_services
        log_end_msg $?
        ;;

    *)
        echo "Usage: $SCRIPTNAME {start|stop|restart|force-reload}" >&2
        exit 1
        ;;
esac

exit 0
