# This file is part of the clacks framework.
#
#  http://clacks-project.org
#
# Copyright:
#  (C) 2010-2012 GONICUS GmbH, Germany, http://www.gonicus.de
#
# License:
#  GPL-2: http://www.gnu.org/licenses/gpl-2.0.html
#
# See the LICENSE file in the project's top-level directory for details.

import os
import gobject #@UnusedImport
import dbus.service
import ConfigParser
import logging
from datetime import datetime
from subprocess import Popen, PIPE
from clacks.common import Environment
from clacks.common.utils import get_timezone_delta
from clacks.common.components import Plugin
from clacks.dbus.utils import get_system_bus


class OptionMissing(Exception):
    pass


class PuppetDBusHandler(dbus.service.Object, Plugin):
    """
    Puppet handler containing methods to be exported to DBUS.

    Configuration keys for section **puppet**

    +------------------+------------+-------------------------------------------------------------+
    + Key              | Format     +  Description                                                |
    +==================+============+=============================================================+
    + report-dir       | String     + Directory where to expect puppet reports to pop up.         |
    +------------------+------------+-------------------------------------------------------------+
    + command          | String     + Path and command to reach puppet.                           |
    +------------------+------------+-------------------------------------------------------------+
    + manifest         | String     + Path to base site manifest.                                 |
    +------------------+------------+-------------------------------------------------------------+

    """

    def __init__(self):
        conn = get_system_bus()
        dbus.service.Object.__init__(self, conn, '/org/clacks/puppet')
        self.env = Environment.getInstance()
        self.log = logging.getLogger(__name__)
        self.logdir = self.env.config.get("puppet.report-dir",
                "/var/log/puppet")

        # Check puppet configuration
        config = ConfigParser.ConfigParser()
        config.read('/etc/puppet/puppet.conf')

        try:
            if config.get("main", "report", "false") != "true":
                raise OptionMissing("puppet has no reporting enabled")

            if config.get("main", "reportdir", "") != self.logdir:
                raise OptionMissing("reportdir configured in " \
                        "/etc/puppet/puppet.conf and %s do not match" % self.env.config.get('core.config'))

            if config.get("main", "reports", "") != "store_clacks":
                raise OptionMissing("storage module probably not compatible")

        except OptionMissing:
            self.hint("configuration section for puppet is incomplete")

        except ConfigParser.NoOptionError:
            self.hint("configuration section for puppet is incomplete")

    def hint(self, msg=""):
        msg += """

Make sure that the main section in /etc/puppet/puppet.conf contains
something like this:

report=true
reportdir=%s
reports=store_clacks
""" % self.logdir
        self.log.warning(msg)

    @dbus.service.method('org.clacks', in_signature='', out_signature='i')
    def dbus_run_puppet(self):
        """ Perform a puppet run using the current configuration """
        self.log.info("executing puppet")

        command = "%s -d %s" % (
            self.env.config.get("puppet.command", default="/usr/bin/puppet"),
            self.env.config.get("puppet.manifest", default="/etc/puppet/manifests/site.pp"),
            )
        self.log.debug("running puppet: %s" % command)

        msg = Popen(command, stdout=PIPE, stderr=PIPE, shell=True).stderr.read()
        hostname = self.env.id

        # Create yaml report in case of critical errors
        if msg != "":
            now = datetime.now()
            ftime = now.strftime("%Y-%m-%d %H:%M:%S.%f %z") + \
                get_timezone_delta()

            # Create structure if missing
            output_dir = self.logdir + "/" + hostname
            if not os.path.exists(output_dir):
                os.makedirs(output_dir)

            # Write yaml file
            output_file = output_dir + "/" + now.strftime("%Y%m%d%H%M.yaml")
            with open(output_file, "w") as f:
                f.write("""--- !ruby/object:Puppet::Transaction::Report
  external_times: {}
  host: %(hostname)s
  logs:
    - !ruby/object:Puppet::Util::Log
      level: !ruby/sym critical
      message: %(message)s
      source: Puppet
      tags:
        - critical
      time: %(time)s
      version: &id001 2.6.0
""" % {'hostname': hostname, 'message': msg, 'time': ftime})

            self.log.error("running puppet failed, see '%s' for more information" % output_file)
            return False

        self.log.debug("running puppet succeeded")
        return True
