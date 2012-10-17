Welcome to the Clacks Project
=============================

The Clacks Project aims to provide a general infrastructure service framework which can
be used for various tasks. It is written in Python and makes use of AMQP messaging for
reliable communication.

Clacks was designed as a backend for the GOsa GUI, but does not depend on it. It has
not been named *GOsa-whatever* to avoid naming confusion.

-----------------------------------------------------------------------------------

Key features
------------

 * **Domain based**

   The AMQP infrastructure is divided into domains. This makes it possible to separate
   different locations by administration logic and/or access control. Clients can be
   "joined" to the domain.

 * **Agent infrastructure with varying plugin set**
  
   Multiple agents can connect to the AMQP infrastructure of your domain but do not
   nessesarily need to provide the same functionality. Message routing will push the
   message to the correct agent.  

 * **Automatic load balancing**

   Plugins provided by more than one agent automatically benefit from automatic load
   balancing.

 * **Extensible client**

   Additionally to agents, clients can be registered/joined to your domain. You can
   simply provide new client functionality by a DBUS/shell proxy. Your clients get
   an automatic inventory which can be stored by an agent interrested in it.

 * **Easy to register RPC methods**

   From the programmers point of view, plugins just need to inherit the Plugin class
   and export their methods using the @Command decorator. This is unique for clients
   and agents.

 * **Message routing**

   The RPC caller does not need to know where the called functionality is provided. It
   automatically reaches the correct location.

 * **XML based eventing system**

   Components can send validated XML events which can be interpreted by other components.
   I.e. an asterisk VoIP call can be signalized on that event bus, and a statistics module
   can subscribe for these events to generate its statistics. 

 * **Object abstraction for various backends**

   The Clacks framework comes with a XML Xquery engine that allows to map certain information
   to various backends. If you - for example - need additional attributes for the predefined
   "User" object, you can simply add them to the object description and "wire" it to target
   attributes in your LDAP or relational database.

 * **SASL and SSL support**

 * **Shell and scripting**

   Every exported method can be easily used inside the Clacks shell or from simple Python
   scripts. Other languages can be used, too. They just need to be able to speak JSONRPC over
   HTTP[S] or AMQP[S].
