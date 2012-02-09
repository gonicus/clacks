#!/bin/bash
SLAPD="/usr/sbin/slapd"
QPIDD="/usr/sbin/qpidd"
QPID_PORT=0
CONF="$PWD/config"
QPID_PORT=60761
LDAP_PORT=60389
HTTP_PORT=60080


start_ldap() {
	sed "s=%(config_dir)s=$CONF=g" $CONF/ldap/slapd.conf.in > $CONF/ldap/slapd.conf
	LDAP_URI="ldap://localhost:$LDAP_PORT"
	$SLAPD -T add -f $CONF/ldap/slapd.conf -l $CONF/ldap/init.ldif &> /dev/null
	$SLAPD -f $CONF/ldap/slapd.conf -h $LDAP_URI
}


stop_ldap() {
	test -f $CONF/data/slapd.pid && kill $(cat $CONF/data/slapd.pid)
	rm $CONF/data/*db* $CONF/data/*lo* $CONF/data/DB_CONFIG $CONF/ldap/slapd.conf
}


start_amqp() {
	export SASL_CONF_PATH=$CONF/amqp/sasl2
	sed "s=%(config_dir)s=$CONF=g" $CONF/amqp/sasl2/qpidd.conf.in > $CONF/amqp/sasl2/qpidd.conf
	sed "s=%(config_dir)s=$CONF=g" $CONF/amqp/qpidd.conf.in > $CONF/amqp/qpidd.conf
	echo -n "secret" | /usr/sbin/saslpasswd2 -cpf $CONF/amqp/qpidd.sasldb -u QPID admin
	[ -f $CONF/amqp/qpidd.log ] && rm $CONF/amqp/qpidd.log
	touch $CONF/amqp/qpidd.log
	$QPIDD --no-data-dir --pid-dir /home/devel/clacks/src/agent/src/tests/config/data -p $QPID_PORT --config $CONF/amqp/qpidd.conf &> /dev/null &
	echo "Waiting for qpid to serve..."
	while true; do
		grep -q "notice Listening on TCP port" $CONF/amqp/qpidd.log && break
		sleep 1
	done
}


stop_amqp() {
	pkill -U $USER qpidd
	rm $CONF/amqp/qpidd.sasldb
	rm $CONF/amqp/qpidd.conf
	rm $CONF/amqp/sasl2/qpidd.conf
}


start_agent() {
	export CLACKS_CONFIG_DIR=$CONF/clacks
	sed -e "s=%(config_dir)s=$CONF=g" -e "s=%(ldap_port)s=$LDAP_PORT=g" -e "s=%(qpid_port)s=$QPID_PORT=g" -e "s=%(http_port)s=$HTTP_PORT=g" $CONF/clacks/config.in > $CONF/clacks/config
	[ -f $CONF/clacks/agent.log ] && rm $CONF/clacks/agent.log
	touch $CONF/clacks/agent.log
	clacks-agent -f &
	echo "Waiting for clacks agent to generate the initial index..."
	while true; do
		grep -q "INFO: index - processed [0-9]* objects in [0-9]*s" $CONF/clacks/agent.log && break
		sleep 1
	done
}


stop_agent() {
	rm -r $CONF/clacks/config $CONF/clacks/database
	pkill -U $USER clacks-agent
}


start_ldap
start_amqp
start_agent

echo "Agent is up and running. Press any key to stop."
read blah
echo "Ok. Shutting down."

stop_agent
stop_amqp
stop_ldap
