Configuration reference
=======================

This section details static configuration switches and runtime settings that
can be used to control the behaviour of the Clacks framework.


Common
******

All configuration flags detailed in this section (can) affect every component
of Clacks: they can be used to configure the *agent* or the *client*, etc.

Command line
------------

These are the common command line flags:

+--------+---------------+------------------------------------------------------------+
+ Short  | Long option   | Description                                                |
+========+===============+============================================================+
+ -c     | ----config    | Path to the configuration file used for this instance of   |
+        |               | Clacks. Note that this is only the base path: it is        |
+        |               | extended by  config  as a plain file and  config.d  as a   |
+        |               | directory containing configuration snippets i.e. for       |
+        |               | specific plugins.                                          |
+--------+---------------+------------------------------------------------------------+
+        | ----url       | URL to the AMQP broker to use.                             |
+--------+---------------+------------------------------------------------------------+
+        | ----profile   | If specified a performance analysis profile is written on  |
+        |               | shutdown.                                                  |
+--------+---------------+------------------------------------------------------------+


Configuration
-------------

Clacks configuration files are written in *ini*-Style. This simplifies editing and
enhances the overview. The common configuration covers a couple of sections detailed
here.

Section **core**
~~~~~~~~~~~~~~~~

+------------------+------------+-------------------------------------------------------------+
+ Key              | Format     +  Description                                                |
+==================+============+=============================================================+
+ base             | String     + The base is the LDAP style base DN where this Clacks        |
+                  |            + entity is responsible for. Example: dc=example,dc=net       |
+------------------+------------+-------------------------------------------------------------+
+ domain           | String     + Domain is the prefix that is used to address AMQP queues    |
+                  |            + and describe access control rules. In contrast to the base  |
+                  |            + keyword, it must only contain plain ASCII characters.       |
+                  |            +                                                             |
+                  |            + As a rule of thumb, we use a reversed domain notation i.e.  |
+                  |            + net.example                                                 |
+------------------+------------+-------------------------------------------------------------+
+ id               | String     + This is the instance ID. It is mandatory and used to connect|
+                  |            + to the AMQP broker.                                         |
+------------------+------------+-------------------------------------------------------------+
+ profile          | Boolean    + Flag to enable profiling.                                   |
+------------------+------------+-------------------------------------------------------------+


Section **amqp**
~~~~~~~~~~~~~~~~

Common AMQP related settings go to the [amqp] section.

+-------------------+------------+-------------------------------------------------------------+
+ Key               | Format     +  Description                                                |
+===================+============+=============================================================+
+ failover          | Boolean    + Flag to determine if automatic failover should be used.     |
+-------------------+------------+-------------------------------------------------------------+
+ key               | String     + The credentials used to connect to the AMQP broker(s).      |
+-------------------+------------+-------------------------------------------------------------+
+ reconnect         | Boolean    + Flag to determine if automatic reconnects should happen.    |
+-------------------+------------+-------------------------------------------------------------+
+ reconnect_interval| Integer    + Time interval to reconnect.                                 |
+-------------------+------------+-------------------------------------------------------------+
+ reconnect_limit   | Integer    + Number of maximum reconnect tries.                          |
+-------------------+------------+-------------------------------------------------------------+
+ url               | String     + The AMQP URL used to connect to a broker - initially.       |
+                   |            + Fallback is done automatically. Format is:                  |
+                   |            + amqp[s]://host.dns-domain:port/clacks-domain                |
+-------------------+------------+-------------------------------------------------------------+
+ worker            | Integer    + Number of workers to process commands.                      + 
+-------------------+------------+-------------------------------------------------------------+

Section **mongo**
~~~~~~~~~~~~~~~~~

The index is maintained in a MongoDB. These are the keys related to connecting
the NoSQL database.

+------------------+------------+-------------------------------------------------------------+
+ Key              | Format     +  Description                                                |
+==================+============+=============================================================+
+ uri              | String     + The hostname / port combination used to connect to the      |
+                  |            + MongoDB. Example: localhost:27017                           |
+------------------+------------+-------------------------------------------------------------+
+ user             | String     + Username used to connect to MongoDB - if required           |
+------------------+------------+-------------------------------------------------------------+
+ password         | String     + Password used to connect to MongoDB - if required           |
+------------------+------------+-------------------------------------------------------------+


Agent
*****

Configuration
-------------

Section **agent**
~~~~~~~~~~~~~~~~~

+------------------+------------+-------------------------------------------------------------+
+ Key              | Format     +  Description                                                |
+==================+============+=============================================================+
+ admins           | String     + Comma separated list of users where the ACL engine is       |
+                  |            + overridden.                                                 |
+------------------+------------+-------------------------------------------------------------+
+ index            | Boolean    +  Flag to enable/disable indexing.                           |
+------------------+------------+-------------------------------------------------------------+
+ node-timeout     | Integer    + Timeout in seconds when an agent is considered 'dead'.      |
+------------------+------------+-------------------------------------------------------------+

Section **amqp**
~~~~~~~~~~~~~~~~

Common AMQP related settings go to the [amqp] section.

+-------------------+------------+-------------------------------------------------------------+
+ Key               | Format     +  Description                                                |
+===================+============+=============================================================+
+ announce          | Boolean    + Publish the service via Zeroconf.                           +
+-------------------+------------+-------------------------------------------------------------+

Section **jsonrpc**
~~~~~~~~~~~~~~~~~~~

+------------------+------------+-------------------------------------------------------------+
+ Key              | Format     +  Description                                                |
+==================+============+=============================================================+
+ path             | String     + Path where JSONRPC over HTTP is hooked in.                  |
+------------------+------------+-------------------------------------------------------------+

Section **http**
~~~~~~~~~~~~~~~~

+------------------+------------+-------------------------------------------------------------+
+ Key              | Format     +  Description                                                |
+==================+============+=============================================================+
+ announce         | Boolean    + Publish the service via Zeroconf.                           +
+------------------+------------+-------------------------------------------------------------+
+ cookie-lifetime  | Integer    + Lifetime of the cookie in seconds.                          |
+------------------+------------+-------------------------------------------------------------+
+ cookie-secret    | String     + Key used to encrypt the cookie.                             |
+------------------+------------+-------------------------------------------------------------+
+ host             | String     + Hostname to bind to / IP to bind to.                        |
+------------------+------------+-------------------------------------------------------------+
+ port             | Integer    + Portnumber to bind to.                                      |
+------------------+------------+-------------------------------------------------------------+
+ ssl              | Boolean    + Flag to tell that we want SSL.                              |
+------------------+------------+-------------------------------------------------------------+
+ certfile         | String     + Path to the certificate.                                    |
+------------------+------------+-------------------------------------------------------------+
+ keyfile          | String     + Path to the key file.                                       |
+------------------+------------+-------------------------------------------------------------+
+ ca-certs         | String     + Path to the CA file.                                        |
+------------------+------------+-------------------------------------------------------------+

Section **scheduler**
~~~~~~~~~~~~~~~~~~~~~

+------------------+------------+-------------------------------------------------------------+
+ Key              | Format     +  Description                                                |
+==================+============+=============================================================+
+ gracetime        | Integer    + Gracetime for foreign jobs before they're assimilated.      +
+------------------+------------+-------------------------------------------------------------+

Section **ldap**
~~~~~~~~~~~~~~~~

+------------------+------------+-------------------------------------------------------------+
+ Key              | Format     +  Description                                                |
+==================+============+=============================================================+
+ bind-secret      | String     + Credentials for the bind user.                              +
+------------------+------------+-------------------------------------------------------------+
+ bind-user        | String     + DN of the bind user.                                        +
+------------------+------------+-------------------------------------------------------------+
+ retry-delay      | String     + Delay before a retry should be done.                        +
+------------------+------------+-------------------------------------------------------------+
+ retry-max        | String     + Maximum of retries before considering connection 'dead'.    +
+------------------+------------+-------------------------------------------------------------+
+ tls              | Boolean    + Use TLS to connect to the LDAP server.                      +
+------------------+------------+-------------------------------------------------------------+
+ url              | String     + URL to connect to - includes the LDAP base.                 +
+------------------+------------+-------------------------------------------------------------+

Backends
--------

Section **backend-sql**
~~~~~~~~~~~~~~~~~~~~~~~

+------------------+------------+-------------------------------------------------------------+
+ Key              | Format     +  Description                                                |
+==================+============+=============================================================+
+ connection       | String     + SQLAlchemy string to connect to a SQL database.             +
+------------------+------------+-------------------------------------------------------------+

Section **backend-json**
~~~~~~~~~~~~~~~~~~~~~~~~

+------------------+------------+-------------------------------------------------------------+
+ Key              | Format     +  Description                                                |
+==================+============+=============================================================+
+ database-file    | String     + Path to the database file that keeps the JSON information.  +
+------------------+------------+-------------------------------------------------------------+

Section **backend-ldap**
~~~~~~~~~~~~~~~~~~~~~~~~

+------------------+------------+-------------------------------------------------------------+
+ Key              | Format     +  Description                                                |
+==================+============+=============================================================+
+ uuid-attribute   | String     + Attribute that keeps the object UUID.                       +
+------------------+------------+-------------------------------------------------------------+
+ create-attribute | String     + Attribute that keeps the creation date.                     +
+------------------+------------+-------------------------------------------------------------+
+ modify-attribute | String     + Attribute that keeps the modification date.                 +
+------------------+------------+-------------------------------------------------------------+
+ pool-filter      | String     + Filter to find nex ID.                                      +
+------------------+------------+-------------------------------------------------------------+

Section **backend-mongodb**
~~~~~~~~~~~~~~~~~~~~~~~~~~~

+------------------+------------+-------------------------------------------------------------+
+ Key              | Format     +  Description                                                |
+==================+============+=============================================================+
+ database         | String     + Name of the MongoDB database.                               +
+------------------+------------+-------------------------------------------------------------+
+ collection       | String     + Name of the MongoDB collection inside the database.         +
+------------------+------------+-------------------------------------------------------------+


Backend monitor
---------------

Section **backend-monitor**
~~~~~~~~~~~~~~~~~~~~~~~~~~~

+------------------+------------+-------------------------------------------------------------+
+ Key              | Format     +  Description                                                |
+==================+============+=============================================================+
+ audit-log        | String     + LDAP audit log file which is scanned for updates.           |
+------------------+------------+-------------------------------------------------------------+
+ modifier         | String     + DN of Clacks configured LDAP managing user.                 |
+------------------+------------+-------------------------------------------------------------+

ACL
---

Managing access control is configuration in the broader sense. You can read more on
this topic in the section :ref:`clacks-acl`.


Client
******

The Clacks client is divided into two parts: the main part and the DBUS part. The client can
be extended thru plugins that may have separate configuration parameters, too:

 * :ref:`Generic DBUS support <client-dbus>`
 * :ref:`DBUS libnotify user notifications <client-notify>`
 * :ref:`Fusioninventory integration <client-fusion>`
 * :ref:`Powermanagement related methods <client-power>`
 * :ref:`Session notifications <client-session>`

Configuration
-------------

Section **client**
~~~~~~~~~~~~~~~~~~

+------------------+------------+-------------------------------------------------------------+
+ Key              | Format     +  Description                                                |
+==================+============+=============================================================+
+ ping-interval    | Integer    + Update ping to the Clacks framework to show: I'm still here.|
+------------------+------------+-------------------------------------------------------------+
+ spool            | String     + Spool directory used for several temporary files.           |
+------------------+------------+-------------------------------------------------------------+

DBUS
****

The DBUS component is the root-component of the Clacks client side. It allows the client
to trigger certain commands as root, but grants non-root operation for the client itself. By
default it comes with a couple of plugins that may have parameters of their own.

 * ref:`Fusioninventory integration <dbus-fusion>`
 * ref:`DBUS libnotify user notifications <dbus-notify>`
 * ref:`Managing unix services <dbus-service>`
 * ref:`Executing shell commands <dbus-shell>`
 * ref:`Wake on lan client <dbus-wakeonlan>`

Configuration
-------------

Section **dbus**
~~~~~~~~~~~~~~~~

+------------------+------------+-------------------------------------------------------------+
+ Key              | Format     +  Description                                                |
+==================+============+=============================================================+
+ script-path      | String     + Script directory that is scanned for DBUS exported scripts. |
+------------------+------------+-------------------------------------------------------------+


--------

TODO


By default it comes with a couple of plugins that may have parameters of their own. 
 
Agent:


Cleanup and add to the documentation 

agent/src/clacks/agent/plugins/gosa/methods.py:                cache_path = self.env.config.get('gosa.cache_path', default="/cache")
agent/src/clacks/agent/plugins/gosa/service.py:        self.path = self.env.config.get('gosa.path', default="/admin")
agent/src/clacks/agent/plugins/gosa/service.py:        self.static_path = self.env.config.get('gosa.static_path', default="/static")
agent/src/clacks/agent/plugins/gosa/service.py:        self.cache_path = self.env.config.get('gosa.cache_path', default="/cache")
agent/src/clacks/agent/plugins/gosa/service.py:        self.ws_path = self.env.config.get('gosa.websocket', default="/ws")
agent/src/clacks/agent/plugins/gosa/service.py:        self.local_path = self.env.config.get('gosa.local', default=spath)
agent/src/clacks/agent/plugins/gosa/service.py:        self.__secret = env.config.get('http.cookie-secret', default="TecloigJink4")
agent/src/clacks/agent/plugins/gosa/service.py:        self.__secret = self.env.config.get('http.cookie-secret', default="TecloigJink4")
agent/src/clacks/agent/plugins/samba/sid.py:            ridbase = int(self.env.config.get('samba.ridbase', default=1000))
agent/src/clacks/agent/plugins/goto/client_service.py:            dn = ",".join(["cn=" + cn, self.env.config.get("goto.machine-rdn",
agent/src/clacks/agent/plugins/goto/client_service.py:        interval = int(self.env.config.get("goto.timeout", default="600"))
agent/src/clacks/agent/plugins/posix/shells.py:        source = env.config.get('goto.shells', default="/etc/shells")

plugins/libinst.boot.preseed/src/libinst/boot/preseed/methods.py:        self.path = self.env.config.get('libinst.path', default="/preseed")
plugins/libinst.boot.preseed/src/libinst/boot/preseed/methods.py:        url = urlparse(self.env.config.get('repository.http_base_url'))
plugins/libinst/src/libinst/manage.py:        self.path = env.config.get('repository.path')
plugins/libinst/src/libinst/manage.py:        db_purge = env.config.get('repository.db_purge')
plugins/libinst/src/libinst/manage.py:            if not self.env.config.get('repository.http_base_url'):
plugins/libinst/src/libinst/manage.py:            result = self.env.config.get('repository.http_base_url')
plugins/libinst/src/libinst/manage.py:        if self.env.config.get("goto.send_uri", "False").upper() == "TRUE":
plugins/libinst/src/libinst/manage.py:            url = parseURL(self.env.config.get("amqp.url"))
plugins/libinst/src/libinst/manage.py:                    self.env.config.get("libinst.template-rdn", "cn=templates,cn=libinst,cn=config"),
plugins/libinst/src/libinst/interface/base.py:            res = conn.search_s(",".join([self.env.config.get("libinst.template-rdn",
plugins/libinst/src/main.py:    repo_path = env.config.get('repository.path')
plugins/libinst.cfg.puppet/src/libinst/cfg/puppet/methods.py:        db_purge = self.env.config.get('repository.db_purge',)
plugins/libinst.cfg.puppet/src/libinst/cfg/puppet/methods.py:            logdir = self.env.config.get("puppet.report-dir",
plugins/libinst.cfg.puppet/src/libinst/cfg/puppet/methods.py:            with open(self.env.config.get("puppet.public_key", default)) as f:
plugins/amires/src/amires/resolver.py:            for opt in env.config.getOptions("resolver-replace"):
plugins/amires/src/amires/resolver.py:                itm = env.config.get("resolver-replace.%s" % opt)
plugins/amires/src/amires/modules/telekom_res.py:            self.priority = float(self.env.config.get("resolver-telekom.priority",
plugins/amires/src/amires/modules/xml_res.py:        filename = self.env.config.get("resolver-xml.filename",
plugins/amires/src/amires/modules/xml_res.py:            self.priority = float(self.env.config.get("resolver-xml.priority",
plugins/amires/src/amires/modules/sugar_res.py:        self.priority = float(self.env.config.get("resolver-sugar.priority",
plugins/amires/src/amires/modules/sugar_res.py:        self.sugar_url = self.env.config.get("resolver-sugar.site_url",
plugins/amires/src/amires/modules/goforge_render.py:        self.forge_url = self.env.config.get("fetcher-goforge.site_url",
plugins/amires/src/amires/modules/ldap_res.py:            self.priority = float(self.env.config.get("resolver-ldap.priority",
plugins/amires/src/amires/modules/doingreport_render.py:        self.whitelisted_users = self.env.config.get("doingreport.users")
plugins/amires/src/amires/modules/doingreport_render.py:        self.forge_url = self.env.config.get("fetcher-goforge.site_url",
plugins/amires/src/amires/modules/clacks_res.py:            self.priority = float(self.env.config.get("resolver-clacks.priority",
plugins/amires/src/amires/main.py:        mw = int(self.env.config.get("amires.avatar_size", default="96"))
plugins/libinst.repo.deb/src/libinst/repo/deb/main.py:                    if not self.env.config.get('repository.rollback') == False and not os.path.exists(rollback_path):
plugins/libinst.repo.deb/src/libinst/repo/deb/main.py:                                    if not self.env.config.get('repository.rollback') == False:
plugins/libinst.repo.deb/src/libinst/repo/deb/main.py:        repository = session.query(Repository).filter_by(path=self.env.config.get('repository.path')).one()
plugins/libinst.cfg.puppet.client/src/libinst/cfg/puppet/client/dbus_main.py:        self.logdir = self.env.config.get("puppet.report-dir",
plugins/libinst.cfg.puppet.client/src/libinst/cfg/puppet/client/dbus_main.py:            if config.get("main", "report", "false") != "true":
plugins/libinst.cfg.puppet.client/src/libinst/cfg/puppet/client/dbus_main.py:            if config.get("main", "reportdir", "") != self.logdir:
plugins/libinst.cfg.puppet.client/src/libinst/cfg/puppet/client/dbus_main.py:            if config.get("main", "reports", "") != "store_clacks":
plugins/libinst.cfg.puppet.client/src/libinst/cfg/puppet/client/dbus_main.py:            self.env.config.get("puppet.command", default="/usr/bin/puppet"),
plugins/libinst.cfg.puppet.client/src/libinst/cfg/puppet/client/dbus_main.py:            self.env.config.get("puppet.manifest", default="/etc/puppet/manifests/site.pp"),
plugins/libinst.cfg.puppet.client/src/libinst/cfg/puppet/client/main.py:        self.__puppet_user = env.config.get("puppet.user",
plugins/libinst.cfg.puppet.client/src/libinst/cfg/puppet/client/main.py:            default=env.config.get("client.user", default="clacks"))
plugins/libinst.cfg.puppet.client/src/libinst/cfg/puppet/client/main.py:        self.__target_dir = env.config.get("puppet.target", default="/etc/puppet")
plugins/libinst.cfg.puppet.client/src/libinst/cfg/puppet/client/main.py:        self.__puppet_command = env.config.get("puppet.command", default="/usr/bin/puppet")
plugins/libinst.cfg.puppet.client/src/libinst/cfg/puppet/client/main.py:        self.__report_dir = env.config.get("puppet.report-dir", default="/var/log/puppet")
plugins/libinst.cfg.puppet.client/src/libinst/cfg/puppet/client/main.py:            'distribution': config.get('release', 'distribution'),
plugins/libinst.cfg.puppet.client/src/libinst/cfg/puppet/client/main.py:            'version': config.get('release', 'version'),
plugins/libinst.cfg.puppet.client/src/libinst/cfg/puppet/client/main.py:            'description': config.get('release', 'description'),
plugins/libinst.cfg.puppet.client/src/libinst/cfg/puppet/client/main.py:        user = self.env.config.get('client.user', default="clacks")


TODO: Fix sample configurations
TODO: gosa plugin data -> qooxdoo-build
