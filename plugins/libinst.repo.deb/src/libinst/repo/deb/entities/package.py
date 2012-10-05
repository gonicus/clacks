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

from sqlalchemy import Column, Integer, String, ForeignKey, Sequence, Text
from sqlalchemy.orm import relationship

from libinst.entities.package import Package

from libinst.entities import UseInnoDB
from libinst.repo.deb.entities.priority import DebianPriority


class DebianPackage(Package, UseInnoDB):
    __tablename__ = 'debian_package'
    __mapper_args__ = {'polymorphic_identity': 'debian_package'}
    id = Column(Integer,
                Sequence('debian_package_id_seq'),
                ForeignKey('package.id'),
                primary_key=True)
    package = relationship(Package, passive_deletes=True)
    source = Column(String(255))
    maintainer = Column(String(255))
    installed_size = Column(String(255))
    depends = Column(Text)
    build_depends = Column(Text)
    format = Column(Text)
    standards_version = Column(Text)
    recommends = Column(Text)
    suggests = Column(Text)
    provides = Column(Text)
    priority_id = Column(Integer, ForeignKey('debian_priority.id'))
    priority = relationship(DebianPriority)
    long_description = Column(Text)

    def __repr__(self):
        return super(DebianPackage, self).__repr__()

    def getInfo(self):
        result = super(DebianPackage, self).getInfo()
        result.update({
            "source": self.source,
            "maintainer": self.maintainer,
            "installed_size": self.installed_size,
            "depends": self.depends,
            "build_depends": self.build_depends,
            "format": self.format,
            "standards_version": self.standards_version,
            "recommends": self.recommends,
            "suggests": self.suggests,
            "provides": self.provides,
            # pylint: disable-msg=E1101
            "priority": None if not self.priority else self.priority.name,
            "long_description": self.long_description,
        })
        return result
