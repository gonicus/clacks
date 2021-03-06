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
import logging
from sqlalchemy import Column, Integer, String, ForeignKey, Sequence, LargeBinary
from sqlalchemy.orm import relationship, backref

from libinst.entities import Base, UseInnoDB
from libinst.entities.distribution import Distribution


class RepositoryDistributions(Base, UseInnoDB):
    __tablename__ = 'repository_distributions'
    distribution = Column(Integer, ForeignKey('distribution.id'), primary_key=True)
    repository = Column(Integer, ForeignKey('repository.id'), primary_key=True)


class RepositoryKeyring(Base, UseInnoDB):
    __tablename__ = 'keyring'
    id = Column(Integer, Sequence('keyring_id_seq'), primary_key=True)
    name = Column(String(255))
    data = Column(LargeBinary())
    passphrase = Column(String(255))


class Repository(Base, UseInnoDB):
    __tablename__ = 'repository'
    id = Column(Integer, Sequence('repository_id_seq'), primary_key=True)
    name = Column(String(255))
    path = Column(String(255), nullable=False, unique=True)
    keyring_id = Column(Integer, ForeignKey('keyring.id'))
    keyring = relationship(RepositoryKeyring)
    # pylint: disable-msg=E1101
    distributions = relationship(Distribution, secondary=RepositoryDistributions.__table__, backref=backref('repository', uselist=False))

    def __repr__(self):
        return self.name if self.name is not None else self.id.__str__()

    def _initDirs(self):
        if not os.path.exists(self.path):
            try:
                os.makedirs(self.path)
            except:
                log = logging.getLogger(__name__)
                log.critical("Could not create directory %s" % self.path)
                raise

        for distribution in self.distributions:
            distribution._initDirs()
