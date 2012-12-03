.. _documentation:


Clacks Framework Documentation
==============================

.. raw:: html

   <div class="active item" style="background-color:white; border: 1px solid #D2D2D2"><iframe style="border:0;" src="_static/clacks-web-compiled.svg" width="920" height="490"></iframe></div>

What is it all about?
---------------------

The Clacks Framework is an AMQP based framework for infrastructure management that
incorporates functionality known from the `GOsa Project <http://oss.gonicus.de/labs/gosa>`_.

AMQP handles the *authentication*, the *message queueing*, the *clustering* and
*load balancing* for us. A client can subscribe to public events using
`XQuery <http://en.wikipedia.org/wiki/XQuery>`_, services (or third parties) can
emit events in a simple manner. AMQP is used by the newly introduced *Clacks agent*
to provide load balanced, clustered services and by several kind of *Clacks client*
applications like a shell, an ordinary client and so on.

Multiple *Clacks agents* create a domain where clients can join or participate in
different ways. Functionality like the new abstraction layer *libinst*, an object
description language, scheduling, etc. are spread over several agents and can be
transparently accessed by clients, thanks to the routing possible with QPID queue
models. The functionality is currently exposed by AMQP and by a HTTP/JSONRPC gateway,
more methods like ReST or SOAP may follow if there's an urgent need for that.

Starting with GOsa 3, there is a `qooxdoo <http://qooxdoo.org>`_ based GUI component
that is 100% build on Clacks.

---------------------

**Contents:**

.. toctree::
   :maxdepth: 3

   start
   downloads
   configuration
   development
   packaging
   license

Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`Command index <cindex>`
* :ref:`search`

