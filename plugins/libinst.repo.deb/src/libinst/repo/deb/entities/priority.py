# -*- coding: utf-8 -*-
from sqlalchemy import Column, Integer, String, Sequence

from libinst.entities import Base, UseInnoDB


class DebianPriority(Base, UseInnoDB):
    __tablename__ = 'debian_priority'
    id = Column(Integer, Sequence('debian_priority_id_seq'), primary_key=True)
    name = Column(String(255))

    def __init__(self, name):
        self.name = name

    def __repr__(self):
        return self.name

    def getInfo(self):
        return {
            "name": self.name,
        }
