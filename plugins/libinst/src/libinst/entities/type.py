# -*- coding: utf-8 -*-
from sqlalchemy import Column, Integer, String, Sequence
from libinst.entities import Base, UseInnoDB


class Type(Base, UseInnoDB):
    __tablename__ = 'type'
    id = Column(Integer, Sequence('type_id_seq'), primary_key=True)
    name = Column(String(255), unique=True)
    description = Column(String(255))

    def __init__(self, name, description=""):
        self.name = name
        self.description = description

    def __repr__(self):
        return self.name

    def getInfo(self):
        return {
            "name": self.name,
            "description": self.description,
        }
