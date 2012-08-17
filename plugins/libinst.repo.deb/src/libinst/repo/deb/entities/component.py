# -*- coding: utf-8 -*-
from libinst.entities import UseInnoDB
from libinst.entities.component import Component


class DebianComponent(Component, UseInnoDB):
    __mapper_args__ = {'polymorphic_identity': 'debian_component'}
