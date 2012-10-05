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
from sqlalchemy import Column, Integer, String, ForeignKey, Sequence, UniqueConstraint, Boolean
from sqlalchemy.orm import relationship, backref
from libinst.entities import Base, UseInnoDB
from libinst.entities.release import Release


class ConfigItemReleases(Base, UseInnoDB):
    __tablename__ = 'config_item_releases'
    config_item = Column(Integer, ForeignKey('config_item.id'), primary_key=True)
    release = Column(Integer, ForeignKey('release.id'), primary_key=True)


class ConfigItem(Base, UseInnoDB):
    __tablename__ = 'config_item'
    id = Column(Integer, Sequence('config_item_id_seq'), primary_key=True)
    name = Column(String(255), nullable=False)
    item_type = Column(String(255))
    path = Column(String(255))
    assignable = Column(Boolean())
    parent_id = Column(Integer, ForeignKey('config_item.id'))
    # pylint: disable-msg=E1101
    release = relationship(Release, secondary=ConfigItemReleases.__table__, backref=backref('config_items'))

    def getPath(self):
        result = []

        if self.parent:
            result.append(self.parent.getPath())

        result = "/" + os.sep.join(result + [self.name]).strip("/")
        return result

    def __repr__(self):
        return "%s -> %s (%s)" % (self.release, self.name, self.item_type)

    def getInfo(self):
        return {
            "name": self.name,
            "item_type": self.item_type,
            "path": self.path,
            "release": None if not self.release else self.relase.name,
        }

    def getAssignableElements(self):
        return {}

ConfigItem.parent = relationship(ConfigItem, remote_side=ConfigItem.id, uselist=False, backref=backref('children', uselist=True))
# pylint: disable-msg=E1101
ConfigItem.__table__.append_constraint(UniqueConstraint('item_type', 'path'))
