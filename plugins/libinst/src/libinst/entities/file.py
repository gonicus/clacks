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

from sqlalchemy import Column, Integer, String, Sequence
from libinst.entities import Base, UseInnoDB


class File(Base, UseInnoDB):
    __tablename__ = 'file'
    id = Column(Integer, Sequence('file_id_seq'), primary_key=True)
    name = Column(String(255))
    size = Column(String(255))
    md5sum = Column(String(255))

    def __repr__(self):
        return self.name

    def getInfo(self):
        return {
            "name": self.name,
            "size": self.size,
            "md5sum": self.md5sum,
        }
