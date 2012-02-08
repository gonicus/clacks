#!/bin/bash
SLAPD="/usr/sbin/slapd"
CONF="$PWD/config"


start_ldap() {
	sed "s=%(config_dir)s=$CONF=g" $CONF/ldap/slapd.conf.in > $CONF/ldap/slapd.conf
	LDAP_URI=$(echo -n "$CONF/data/ldapi" | sed 's/\//%2F/g')
	$SLAPD -T add -f $CONF/ldap/slapd.conf -l $CONF/ldap/init.ldif
	$SLAPD -f $CONF/ldap/slapd.conf -h ldapi://%2F$LDAP_URI
}


stop_ldap() {
	test -f $CONF/data/slapd.pid && kill $(cat $CONF/data/slapd.pid)
	rm $CONF/data/*db* $CONF/data/*lo* $CONF/data/DB_CONFIG $CONF/ldap/slapd.conf
}

start_ldap
stop_ldap
