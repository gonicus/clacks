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

from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()


class UseInnoDB(object):
    __table_args__ = {'mysql_engine': 'InnoDB'}

__import__('pkg_resources').declare_namespace(__name__)
