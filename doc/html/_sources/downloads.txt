Downloads
=========

Clacks is currently under heavy development, so there are now final versions around right
now. What there is, actually, are preliminary Debian packages, OVAs for playing around and
of course the obligatory github links.

Virtual appliances
------------------

There are two appliances that can be imported to your OVA capable virtualization solution
(i.e. Virtual Box). You can use them to play around with a single agent and a client inside
of your home network. Everything is more or less ready to use.

* **Agent OVA (~1,2GiB)**

  The agent consists of: clacks-agent, LDAP, AMQP, DBXML and some sample data to get stuff running.

  `Download agent OVA (04. February 2012) <http://clacks-project.org/downloads/ClacksInfrastructureServer-20120204.ova>`_


* **Client OVA (~1,1GiB)**

  The client consists of: clacks-client and some test stuff like the graphical join dialog.

  `Download client OVA (04. February 2012) <http://clacks-project.org/downloads/ClacksClient-20120204.ova>`_

Packages
--------

There are no pre-built packages available in the moment. This will be started from the first beta on.

You can easily build your own packages using these commands::

   $ git clone git://github.com/clacks/clacks.git
   $ cd clacks/contrib/packaging/debian/clacks
   $ ./package.sh
   $ cd clacks-<version>
   $ dpkg-buildpackage -us -uc -rfakeroot

Keep in mind that these package may not be 100% "in shape", because the packaging is not updated
regulary until the beta is out.


Developers
----------

The project is mirrored to github. This means that you can clone it using::

    git://github.com/clacks/clacks.git


