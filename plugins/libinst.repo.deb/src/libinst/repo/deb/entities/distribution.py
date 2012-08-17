# -*- coding: utf-8 -*-
import gettext
from sqlalchemy import Column, Integer, String, ForeignKey, Sequence
from libinst.entities import UseInnoDB
from libinst.entities.distribution import Distribution
from pkg_resources import resource_filename #@UnresolvedImport

# Include locales
t = gettext.translation('messages', resource_filename("libinst.repo.deb", "locale"), fallback=True)
_ = t.ugettext


class DebianDistribution(Distribution, UseInnoDB):
    __tablename__ = 'debian_distribution'
    __mapper_args__ = {'polymorphic_identity': 'debian_distribution'}
    id = Column(Integer,
                Sequence('debian_distribution_id_seq'),
                ForeignKey('distribution.id'),
                primary_key=True)
    debian_security = Column(String(255))
    debian_volatile = Column(String(255))

    def getInfo(self):
        result = super(DebianDistribution, self).getInfo()
        result.update({
            "debian_security": self.debian_security,
            "debian_volatile": self.debian_volatile,
        })
        return result
