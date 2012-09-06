# -*- coding: utf-8 -*-
from sqlalchemy import Column, Integer, String, Sequence
from libinst.entities import Base, UseInnoDB


class Section(Base, UseInnoDB):
    __tablename__ = 'section'
    id = Column(Integer, Sequence('section_id_seq'), primary_key=True)
    description = Column(String(255))
    name = Column(String(255), unique=True)

    def __init__(self, name):
        self.name = name

    def __repr__(self):
        return self.name

    def getInfo(self):
        return {
            "name": self.name,
            "description": self.description,
        }
