# -*- coding: utf-8 -*-
import cgi


def mr(data):
    try:
        return data.decode("utf-8")
    except:
        try:
            return data.decode("raw_unicode_escape").encode("utf-8")
        except:
            try:
                return data.encode("raw_unicode_escape").decode("utf-8")
            except:
                return data


class BaseRenderer(object):

    priority = 1

    def __init__(self):
        pass


    def getHTML(self, particiantInfo, selfInfo, event):
        if not particiantInfo:
            raise RuntimeError("particiantInfo must not be None.")
        if type(particiantInfo) is not dict:
            raise TypeError("particiant Info must be a dictionary.")
