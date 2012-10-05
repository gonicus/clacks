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

from libinst.entities import UseInnoDB
from libinst.entities.component import Component


class DebianComponent(Component, UseInnoDB):
    __mapper_args__ = {'polymorphic_identity': 'debian_component'}
