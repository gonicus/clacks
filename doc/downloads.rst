Downloads
=========

You can download pre-build packages, virtual machine appliances for testing or
- of course - use an obligatory github clone.

Packages
--------

Debian / Ubuntu
^^^^^^^^^^^^^^^

There are pre-build packages for Debian (wheezy+) and Ubuntu (12.04+) available. Please
add ::

  deb http://apt.gonicus.de/debian wheezy clacks

in */etc/apt/sources.list.d/clacks.list*, run ::

  $ sudo apt-get update
  $ sudo apt-get install gonicus-keyring
  $ sudo apt-get update

Then you can install the packages

  * clacks-agent
  * clacks-client
  * clacks-shell

Depending on what you want to do.

.. note::
   Note that *agent* and *client* packages are **not** combinable in the moment.


Developers
----------

The project is mirrored to `github <http://github.com/gonicus/clacks>`_. This means that you can clone it using::

    $ git clone git://github.com/gonicus/clacks.git

Also initialize the submodules::

    $ git submodules init
    $ git submodules update


Virtual appliances
------------------

There are two appliances that can be imported to your OVA capable virtualization solution
(i.e. Virtual Box). You can use them to play around with a single agent and a client inside
of your home network. Everything is more or less ready to use.

* **Agent OVA (~1,2GiB)**

  The agent consists of: clacks-agent, LDAP, AMQP, DBXML, GOsa and some sample data to get stuff running.

  `Download agent OVA (30. October 2012) <http://clacks-project.org/downloads/ClacksInfrastructureServer-20121030.ova>`_


* **Client OVA (~1,1GiB)**

  The client consists of: clacks-client and some test stuff like the graphical join dialog.

  `Download client OVA (04. February 2012) <http://clacks-project.org/downloads/ClacksClient-20120204.ova>`_

