Getting started
===============

.. _quickstart:

This document contains information on *how to get started* with
the current Clacks framework - version 0.8.

Using pre-built packages
------------------------

Currently there are only Debian/Ubuntu packages available for the Clacks
framework. Additionally you need at least Wheezy/12.04 to proceed.

.. information::

    Older versions of Debian/Ubuntu do not have the required package versions
    installed. Installations may work using backports and/or re-building


APT repository
^^^^^^^^^^^^^^

Please create a new file under /etc/apt/sources.list.d/clacks.list and place
the following content inside::

   deb http://debian.gonicus.de/debian wheezy Clacks stable

Now install the key package::

   $ sudo apt-get install gonicus-keyring

The installer will report an untrusted package - which is ok in this case,
because it *contains* the GONICUS signing key. It is used to sign the packages
we'll download in the next step.


Installing a Clacks agent
^^^^^^^^^^^^^^^^^^^^^^^^^

To use the Clacks framework, you need at least one agent that loads some
plugins and provides the base communication framework. Compared to the
client and the shell, the agent is the part that needs most supplying
services.

.. warning::

  Until we reach version 1.0, you can only use one agent.


For the first node, install *QPID*, *LDAP* and *MongoDB*::
  
  $ sudo apt-get install qpidd mongodb-server slapd ldap-utils sasl2-bin

Memorize the user and passwords you've used for LDAP. MongoDB is just
fine and can be configured to only run locally for now.

To proceed, you have to perform the actions detailed in:

:status: todo
	Insert links

 * Setting up LDAP
 * Setting up QPID

If this is fine, copy over the configuration file for the Clacks agent to
/etc/clacks/config and adapt the settings to match the ones for your site::
  
  $ sudo install -o root -g clacks -m 0640 /usr/share/doc/clacks-agent/examples/config /etc/clacks/config
  $ sudo vi /etc/clacks/config

At least adapt the node-name to fit the current host name of your server
and the LDAP credentials that you've created in **Setting up LDAP**.

No you can start the agent using::
  
  $ sudo supervisorctl start clacks-agent

Watch out for errors in */var/log/clacks.log*. If everything went up well,
the agent starts indexing your LDAP and you might see some warnings about
not recognized objects.

After the agent is up and running, you should define a couple of ACL sets
in order to get rid of the initial ACL override in your Clacks configuration.

:status: todo
	Insert links

Please take a look at 'Configuring access control'.


Installing a Clacks client
^^^^^^^^^^^^^^^^^^^^^^^^^^

Clacks clients are nodes that you want to have *under the hood* in some form. They
are monitored, inventorized using fusioninventory (optionally) and can be controlled
in various ways. Controlling addresses topics like *config management* (i.e. using puppet),
*system states* (reboot, wake on lan, etc.), user notifications and executing certain
commands as **root** on these systems.

To install the client you need to work thru two steps. First, install it (the
example includes the inventory part)::
    
  $ sudo apt-get install clacks-client fusioninventory-agent

The client tries to start, but will fail due to missing configurations, so the
second step is to generate a configuration - aka *joining* the client to the
Clacks domain. May sound familiar to Microsoft users.

.. warning::

  In the current version, it is only possible to do an *active* join. The former
  GOsa client *incoming* mechanism is currently beeing implemented and not usable
  right now.

Joining is easy::

  $ sudo clacks-join

It will first search for an active agent. Then you'll have to provide the credentials
of a user that is allowed to join the client (i.e. the administrator you've initially
created).

.. information::

  Maybe the zeroconf mechanism that is used to find an agent is not working
  in your setup. In this case use the *--url* switch to provide the complete
  AMQP URL. Example::
    
    $ sudo clacks-join --url amqps://agent.example.net/net.example

If this succeeds, a configuration file is created automatically and you can start the
client::
  
  $ sudo supervisorctl start clacks-client

If everything went fine, the client is up and running. You'll see some messages
in the agent's log and the client log for that. As for servers, messages find their
way to */var/log/clacks.log*.

.. information::

  Joining requires at least one active agent.

Note that while it is technically no problem to run both - a client and an agent -- on the
same physical node, it is not supported by the packages in the moment.


Installing the shell
^^^^^^^^^^^^^^^^^^^^

Compared to agents and clients, the shell installation is trivial::

  $ sudo apt-get install clacks-shell

Just try to run it::
  
  $ clacksh
  Searching service provider...
  Connected to https://amqp.example.net:8080/rpc
  Username [cajus]:
  Password:
  Clacks infrastructure shell. Use Ctrl+D to exit.
  >>> clacks.help()
  ...


Without pre-built packages
--------------------------

Common setup
^^^^^^^^^^^^

System prerequisites
""""""""""""""""""""

To run the services in the designed way later on, you need a special user
and a couple of directories::

    $ sudo adduser --system --group clacks --home=/var/lib/clacks

If you're going to run the service in daemon mode, please take care that
there's a */var/run/clacks* for placing the PID files.


Python prerequisites
""""""""""""""""""""

While we try to keep everything inside a virtual python environment for
development, some of the python modules need compilation - which rises the
number of required packages drastically. For the time being, please install
the following packages in your system::

  $ sudo apt-get install python2.7-dev python-dumbnet python-avahi python-virtualenv \
         libavahi-compat-libdnssd-dev python-openssl python-dbus libssl-dev python-gtk2 \
         python-lxml python-libxml2 python-dmidecode python-ldap python-nose \
         python-kid python-coverage python-dateutil python-smbpasswd python-netifaces \
         sasl2-bin python-cjson

.. note::
      On MS Windows systems, only the client is supposed to work. Please install the
      pywin32 package: http://sourceforge.net/projects/pywin32/


Setup a virtual environment for playing with clacks 1.0 alpha
"""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""

As a non-root user, initialize the virtual environment::

  $ virtualenv --setuptools --system-site-packages --python=python2.7  clacks
  $ cd clacks
  $ source bin/activate


Obtaining the source
""""""""""""""""""""

For now, please use git::

   $ cd 'the place where you created the clacks virtualenv'
   $ git clone git://oss.gonicus.de/git/gosa.git src

Additionally, you can get some stripped of Clacks 2.7 sources from here::

   $ git clone git://oss.gonicus.de/git/gosa-gui.git
   $ cd gosa-gui
   $ git submodule init
   $ git submodule update

This will place all relevant files inside the 'src' directory.

.. warning::
      The "source bin/activate" has to be done every time you work in or with the
      virtual environment. Stuff will fail if you don't do this. If you're asked for
      sudo/root, you're doing something wrong.


The clacks agent
^^^^^^^^^^^^^^^^

To run the agent, you most likely need a working AMQP broker and
a working LDAP setup.


Prerequisites
"""""""""""""

We use qpidc as the AMQP broker. Other implementations like rabbitmq,
etc. are not supported. They lack some functionality we're making use
of.


Adding the AMQP repository
""""""""""""""""""""""""""

In Debian, the simpliest way to get qpid running would be the use
of an existing repository. Include it in your configuration like this::

  # wget -O - http://apt.gonicus.de/archive.key | apt-key add -
  # [ -d /etc/apt/sources.list.d ] || mkdir /etc/apt/sources.list.d
  # echo "deb http://apt.gonicus.de/debian/ squeeze main" > /etc/apt/sources.list.d/gonicus.list
  # apt-get update


Install qpid broker and clients
"""""""""""""""""""""""""""""""

::

  # apt-get install qpidd qpid-client qpid-tools

After qpid has been installed, you may modify the access policy
to fit the clacks-agent needs a `/etc/qpid/qpidd.acl` containing::

	# QPID policy file
	#
	# User definition:
	#   user = <user-name>[@domain[/realm]]
	#
	# User/Group lists:
	#   user-list = user1 user2 user3 ...
	#   group-name-list = group1 group2 group3 ...
	#
	# Group definition:
	#   group <group-name> = [user-list] [group-name-list]
	#
	# ACL definition:
	#   permission = [allow|acl|deny|deny-log]
	#   action = [consume|publish|create|access|bind|unbind|delete|purge|update]
	#   object = [virtualhost|queue|exchange|broker|link|route|method]
	#   property = [name|durable|owner|routingkey|passive|autodelete|exclusive|type|alternate|queuename|schemapackage|schemaclass]
	#
	# acl permission {<group-name>|<user-name>|"all"} {action|"all"} [object|"all"] [property=<property-value>]
	#
	# Example:
	#
	# group client = user1@QPID user2@QPID
	# acl allow client publish routingkey=exampleQueue exchange=amq.direct
	#
	# Will allow the group "client" containing of "user1" and "user2" be able to
	# make use of the routing key "exampleQueue" on the "amq.direct" exchange.
	
	# Group definitions
	group admins admin@QPID cajus@QPID
	group agents amqp@QPID
	#group event-publisher agents admins
	#group event-consumer agents admins
	group event-consumer amqp@QPID
	group event-publisher amqp@QPID
	
	# Admin is allowed to do everything
	acl allow admins all
	
	# Reply queue handling
	acl allow all access exchange name=reply-*
	acl allow all access queue name=reply-* owner=self
	acl allow all create queue name=reply-* durable=false autodelete=true
	acl allow all consume queue name=reply-* owner=self
	acl allow all publish exchange routingkey=reply-* owner=self
	
	# Event producer
	acl allow event-publisher all     queue    name=org.clacks
	acl allow event-publisher all     exchange name=org.clacks
	
	# Event consumer
	#TODO: replace "all" by "event-consumer" later on
	acl allow all create  queue    name=event-listener-*
	acl allow all delete  queue    name=event-listener-* owner=self
	acl allow all consume queue    name=event-listener-* owner=self
	acl allow all access  queue    name=event-listener-* owner=self
	acl allow all purge   queue    name=event-listener-* owner=self
	acl allow all access  queue    name=org.clacks
	acl allow all access  exchange name=org.clacks
	acl allow all access  exchange name=event-listener-* owner=self
	acl allow all bind    exchange name=org.clacks queuename=event-listener-* routingkey=event
	acl allow all unbind  exchange name=org.clacks queuename=event-listener-* routingkey=event
	acl allow all publish exchange name=org.clacks routingkey=event
	
	# Let agents do everything with the org.clacks queues and exchanges, agents itself
	# are trusted by now.
	acl allow agents all queue name=org.clacks.*
	acl allow agents all exchange name=org.clacks.*
	acl allow agents all exchange name=amq.direct queuename=org.clacks.*
	
	# Let every authenticated instance publish to the command queues
	acl allow all access   queue    name=org.clacks.command.*
	acl allow all publish  queue    name=org.clacks.command.*
	acl allow all publish  exchange routingkey=org.clacks.command.*
	acl allow all access   exchange name=org.clacks.command.*
	
	# Let clients create their own queue to listen on
	acl allow all access  queue    name=org.clacks
	acl allow all access  queue    name=org.clacks.client.* owner=self
	acl allow all consume queue    name=org.clacks.client.* owner=self
	acl allow all create  queue    name=org.clacks.client.* exclusive=true autodelete=true durable=false
	acl allow all access  exchange name=org.clacks
	acl allow all access  exchange name=org.clacks.client.* owner=self
	acl allow all bind    exchange name=amq.direct queuename=org.clacks.client.*
	
	# Let agents send to the client queues
	acl allow agents publish  exchange  routingkey=org.clacks.client.*
	
	# By default, drop everything else
	acl deny all all

Now the broker aka bus is up and running on the host.


For production use, you should enable SSL for the broker and for clacks core. Generating
the certificates is shown here:

http://rajith.2rlabs.com/2010/03/01/apache-qpid-securing-connections-with-ssl/


Install LDAP service
""""""""""""""""""""

To use the LDAP service, a couple of schema files have to be added to
your configuration. The following text assumes that you've a plain / empty
stock debian configuration on your system. If it's not the case, you've to
know what to do yourself.

First, install the provided schema files. These commands have to be executed
with *root* power by default, so feel free to use sudo and find the schema
*LDIF* files in the ``contrib/ldap`` directory of your clacks checkout. Install
these schema files like this::

	# ldapadd -Y EXTERNAL -H ldapi:/// -f clacks-core.ldif
	# ldapadd -Y EXTERNAL -H ldapi:/// -f registered-device.ldif
	# ldapadd -Y EXTERNAL -H ldapi:/// -f installed-device.ldif
	# ldapadd -Y EXTERNAL -H ldapi:/// -f configured-device.ldif

If you use the PHP GUI, you also need to install the "old" schema files, because
the Clacks GUI and clacks.agent service are meant to coexist until everything is cleanly
migrated.

After you've optionally done that, find out which base is configured for your system::

	manager@ldap:~$ sudo ldapsearch -LLL -Y EXTERNAL -H ldapi:/// -b cn=config olcSuffix=* olcSuffix
	SASL/EXTERNAL authentication started
	SASL username: gidNumber=0+uidNumber=0,cn=peercred,cn=external,cn=auth
	SASL SSF: 0
	dn: olcDatabase={1}hdb,cn=config
	olcSuffix: dc=example,dc=net

In this case, you'll see the configured suffix as **dc=example,dc=net** in the
result set. Your milieage may vary.

Based on the suffix, create a *LDIF* file containing an updated index - on top with
the *DN* shown in the result of the search above::

	dn: olcDatabase={1}hdb,cn=config
	changetype: modify
	replace: olcDbIndex
	olcDbIndex: default sub
	olcDbIndex: objectClass pres,eq
	olcDbIndex: cn pres,eq,sub
	olcDbIndex: uid eq,sub
	olcDbIndex: uidNumber eq
	olcDbIndex: gidNumber eq
	olcDbIndex: mail eq,sub
	olcDbIndex: deviceStatus pres,sub
	olcDbIndex: deviceType pres,eq
	olcDbIndex: sn pres,eq,sub
	olcDbIndex: givenName pres,eq,sub
	olcDbIndex: ou pres,eq,sub
	olcDbIndex: memberUid eq
	olcDbIndex: uniqueMember eq
	olcDbIndex: deviceUUID pres,eq

Save that file to *index-update.ldif* and add it to your LDAP using::

	manager@ldap:~$ sudo ldapmodify -Y EXTERNAL -H ldapi:/// -f index-update.ldif

Your LDAP now has the required schema files and an updated index to perform
searches in reliable speed.

Later in this document, you'll need the *DN* and the *credentials* of the LDAP administrator
which has been created during the setup process. For Debian, this is *cn=admin,<your base here>*.

.. note::

	Hopefully, you remember the credentials you've assigned during LDAP
	installation, because you'll need them later on ;-)


AMQP LDAP-Authentication
""""""""""""""""""""""""

/etc/default/saslauthd::

  #
  # Settings for saslauthd daemon
  # Please read /usr/share/doc/sasl2-bin/README.Debian for details.
  #
  
  # Should saslauthd run automatically on startup? (default: no)
  START=yes
  
  # Description of this saslauthd instance. Recommended.
  # (suggestion: SASL Authentication Daemon)
  DESC="SASL Authentication Daemon"
  
  # Short name of this saslauthd instance. Strongly recommended.
  # (suggestion: saslauthd)
  NAME="saslauthd"
  
  # Which authentication mechanisms should saslauthd use? (default: pam)
  #
  # Available options in this Debian package:
  # getpwent  -- use the getpwent() library function
  # kerberos5 -- use Kerberos 5
  # pam       -- use PAM
  # rimap     -- use a remote IMAP server
  # shadow    -- use the local shadow password file
  # sasldb    -- use the local sasldb database file
  # ldap      -- use LDAP (configuration is in /etc/saslauthd.conf)
  #
  # Only one option may be used at a time. See the saslauthd man page
  # for more information.
  #
  # Example: MECHANISMS="pam"
  MECHANISMS="ldap"
  
  # Additional options for this mechanism. (default: none)
  # See the saslauthd man page for information about mech-specific options.
  MECH_OPTIONS=""
  
  # How many saslauthd processes should we run? (default: 5)
  # A value of 0 will fork a new process for each connection.
  THREADS=5
  
  # Other options (default: -c -m /var/run/saslauthd)
  # Note: You MUST specify the -m option or saslauthd won't run!
  #
  # WARNING: DO NOT SPECIFY THE -d OPTION.
  # The -d option will cause saslauthd to run in the foreground instead of as
  # a daemon. This will PREVENT YOUR SYSTEM FROM BOOTING PROPERLY. If you wish
  # to run saslauthd in debug mode, please run it by hand to be safe.
  #
  # See /usr/share/doc/sasl2-bin/README.Debian for Debian-specific information.
  # See the saslauthd man page and the output of 'saslauthd -h' for general
  # information about these options.
  #
  # Example for postfix users: "-c -m /var/spool/postfix/var/run/saslauthd"
  OPTIONS="-c -m /var/run/saslauthd"


/etc/saslauthd.conf::

  ldap_servers: ldap://ldap.your.domain
  ldap_search_base: dc=example,dc=com
  ldap_filter: (|(&(objectClass=simpleSecurityObject)(cn=%U))(&(objectClass=gosaAccount)(uid=%U))(&(objectClass=registeredDevice)(deviceUUID=%U)))
  ldap_scope: sub
  ldap_size_limit: 0
  ldap_time_limit: 15
  ldap_timeout: 15
  ldap_version: 3
  ldap_debug: 255


Test::

  # /etc/init.d/saslauthd restart
  # testsaslauthd -u admin -p secret -r QPID


/etc/qpid/sasl/qpidd.conf::

  pwcheck_method: saslauthd
  mech_list: PLAIN LOGIN

Start up service::

  # adduser qpidd sasl
  # /etc/init.d/qpidd restart

Check if it works::

  # qpid-config -a admin/secret@hostname queues

Prepare DNS-Zone for zeroconf
"""""""""""""""""""""""""""""

Zeroconf setup::

  ; Zeroconf base setup
  b._dns-sd._udp                  PTR @   ;  b = browse domain
  lb._dns-sd._udp                 PTR @   ;  lb = legacy browse domain
  _services._dns-sd._udp          PTR _amqps._tcp
                                  PTR _https._tcp
  
  ; Zeroconf clacks records
  _amqps._tcp                     PTR Clacks\ RPC\ Service._amqps._tcp
  Clacks\ RPC\ Service._amqps._tcp  SRV 0 0 5671 amqp.intranet.gonicus.de.
                                  TXT path=/org.clacks service=clacks
  
  _https._tcp                     PTR Clacks\ Web\ Service._https._tcp
                                  PTR Clacks\ RPC\ Service._https._tcp
  Clacks\ Web\ Service._https._tcp  SRV 0 0 443 gosa.intranet.gonicus.de.
                                  TXT path=/gosa
  Clacks\ RPC\ Service._https._tcp SRV 0 0 8080 amqp.intranet.gonicus.de.
                                  TXT path=/rpc service=clacks

You can test your setup with::

  you@amqp:~$ avahi-browse -D
  +  n/a  n/a example.net

  you@amqp:~$ avahi-browse -rd example.net _amqps._tcp
  +   k.A. k.A. Clacks RPC Service                              _amqps._tcp          example.net
  =   k.A. k.A. Clacks RPC Service                              _amqps._tcp          example.net
     hostname = [amqp.example.net]
     address = [10.3.64.59]
     port = [5671]
     txt = ["service=clacks" "path=/org.clacks"]


Deploy a development agent
""""""""""""""""""""""""""

To deploy the agent, please run these commands inside the activated
virtual environment::

  $ pushd .; cd clacks.common && ./setup.py develop; popd
  $ pushd .; cd clacks.agent && ./setup.py develop; popd


  Alternatively you can build the complete package using::

  $ ./setup.py develop


.. warning:: 
	Using the above command to build the complete package will also build
	additional modules like libinst, amires, ... 

     	This will increase the configuration effort drastically, which is not 
	recommended during the quickstart quide.


Starting the service
""""""""""""""""""""

In a productive environment, everything should be defined in the configuration
file, so copy the configuration file to the place where clacks expects it::

  $ mkdir -p /etc/clacks
  $ cp ./src/clacks.agent/src/clacks/agent/data/agent.conf /etc/clacks/config

Now take a look at the config file and adapt it to your needs.

You can start the daemon in foreground like this::

  $ clacks-agent -f

.. warning::
    Make sure, you've entered the virtual environment using "source bin/activate"
    from inside the clacks directory.


If you want to run the agent in a more productive manner, you can use the
daemon mode and start it as root. It will then fork to the configured user
and run as a daemon.


:status: todo
	Describe how to secure the communication between the clacks-agent and used services.


Here is an example config file for a non-secured service. (A HowTo about securing the service will follow soon!)::

    [core]
    
    # Keyword loglevel: ALL/DEBUG, INFO, WARNING, ERROR, CRITICAL
    loglevel = DEBUG
    
    # Keyword syslog: file, stderr, syslog
    log = stderr
    
    # Keyword logfile: full path to log to if log = file
    #logfile = /var/log/clacks/agent.log
    
    # Keyword id: name of this clacks-agent node
    id = clacks-agent
    
    # Keyword user: username to run the daemon as
    #user = clacks
    
    # Keyword group: groupname to run the daemon as
    #group = clacks
    
    # Keyword pidfile: where to place the pid in daemon mode
    #pidfile = /var/run/clacks/clacks.pid
    
    # Keyword profile: for debugging, only
    profile = False

    [scheduler]
    database = sqlite://
    
    [amqp]
    
    # Keyword url: URL to one of your AMQP servers
    #
    # Examples:
    #
    # amqp://amqp.example.net:5671
    # amqps://amqp.example.net:5671
    #
    # Secured services listing on 5672!
    # This example uses an unsecured amqp service
    url = amqp://localhost:5672
    
    # Keyword id:
    id = admin
    key = tester
    
    [http]
    host = localhost
    port = 8080
    #sslpemfile = /etc/clacks/host.pem
    
    [goto]
    oui-db = /usr/share/clacks/oui.txt
    
    [repository]
    database = mysql+mysqldb://libinst:secret@localhost/libinst?charset=utf8&use_unicode=0
    http_base_url = http://localhost/debian
    db_purge = False
    path = /srv/repository/data
    
    [ldap]
    url = ldap://localhost/dc=example,dc=net
    bind_dn = cn=admin,dc=example,dc=net
    bind_secret = secret
    pool_size = 10



The clacks shell
^^^^^^^^^^^^^^^^

Installing
""""""""""

To deploy the shell, use::

  $ pushd .; cd clacks.common && ./setup.py develop; popd
  $ pushd .; cd clacks.shell && ./setup.py develop; popd

inside your activated virtual env. You can skip this if you ran ./setup.py for
a complete deployment.


First contact
^^^^^^^^^^^^^

The clacks shell will use zeroconf/DNS to find relevant connection methods. Alternatively
you can specify the connection URL to skip zeroconf/DNS.

Start the shell and send a command::

  $ clacksh
  (authenticate as the admin user you've created in qpid's SASL DB)
  >>> clacks.help()
  >>> mksmbhash("secret")
  >>> <Strg+D>

The shell did not get priorized work in the moment, so the clacks.help() output is
neither sorted, nor grouped by plugins. Much space for improvements.

If you tend to use a connection URL directly, use::

  $ clacksh http[s]://amqp.example.com:8080/rpc

for HTTP based sessions or ::

  $ clacksh amqp[s]://amqp.example.com/org.clacks

for AMQP based sessions.


The clacks client
^^^^^^^^^^^^^^^^^^

A clacks client is a device instance that has been joined into the clacks network.
Every client can incorporate functionality into the network - or can just be
a managed client.


Installing
""""""""""

To deploy the client components, use::

  $ pushd .; cd clacks.common && ./setup.py develop; popd
  $ pushd .; cd clacks.client && ./setup.py develop; popd
  $ pushd .; cd clacks.dbus && ./setup.py develop; popd

inside your activated virtual env. You can skip this if you ran ./setup.py for
a complete deployment.


Joining the party
"""""""""""""""""

A client needs to authenticate to the clacks bus. In order to create the required
credentials for that, you've to "announce" or "join" the client to the system.

To do that, run ::

  $ sudo -s
  # cd 'wherever your clacks virtual environment is'
  # source bin/activate
  # clacks-join

on the client you're going to join. In the development case, this may be the
same machine which runs the agent.


Running the root component
""""""""""""""""""""""""""

Some functionality may need root permission, while we don't want to run the complete
client as root. The clacks-dbus component is used to run dedicated tasks as root. It
can be extended by simple plugins and registers the resulting methods in the dbus
interface.

To use the dbus-component, you've to allow the clacks system user (or whatever user
the clacks-client is running later on) to use certain dbus services. Copy and eventually
adapt the file src/contrib/dbus/org.clacks.conf to /etc/dbus-1/system.d/ and
reload your dbus service. ::

  $ sudo service dbus reload

To start the dbus component, activate the python virtual environment as root and run
the clacks-dbus component in daemon or foreground mode::

  $ sudo -s
  # cd 'wherever your clacks virtual environment is'
  # source bin/activate
  # clacks-dbus -f


Running the client
""""""""""""""""""

To run the client, you should put your development user into the clacks group - to
be able to use the dbus features::

  $ sudo adduser $USER clacks

You might need to re-login to make the changes happen. After that, start the clacks
client inside the activated virtual environment::

  $ clacks-client -f

Integration with PHP Clacks
---------------------------

The *clacks agent* and *clacks client* setup may be ok for playing around, but
as of Clacks 2.7 you can configure an active communication between the ordinary
PHP Clacks and the agent - which acts as a replacement for *gosa-si*.

.. warning::

   While the clacks agent series are under heavy development, it is recommended
   to try with Clacks 2.7 trunk. You should be aware of not beeing able to replace
   all gosa-si functionality in the moment.

-----------------

To connection the web-based Clacks with the clacks agent you have to adjust the configuration slightly.
There are two ways to do so, the first is to update the Clacks 2.7 configuration file directly 
``/etc/clacks/config`` to include the following lines:

.. code-block:: xml

    <main>
    	...
        <location 
            gosaRpcPassword="secret"
            gosaRpcServer="https://gosa-agent-server:8080/rpc"
            gosaRpcUser="amqp"/>
    </main>


The other way would be to configure these properties inside of Clacks using the ``preferences`` plugin.

Select the ``preferences`` plugin from the menu and then read and accept the warning message.

.. image:: static/images/gosa_setup_rpc_1.png

Then click on the filter rules and select "All properties" to show all properties, even unused.
Then enter ``rpc`` in the search-filter input box, to only show rpc related options, only three options should 
be left in the list below. 
Now adjust the values of these properties to match your setup and click ``apply`` on the bottom of the page.

.. image:: static/images/gosa_setup_rpc_2.png

That is all, you may only need to relog into the Clacks GUI.

Design overview
---------------

**TODO**: graphics, text, etc.
