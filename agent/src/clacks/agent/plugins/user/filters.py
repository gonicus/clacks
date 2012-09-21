# -*- coding: utf-8 -*-
import os
import StringIO
import Image, ImageOps
from clacks.agent.objects.filter import ElementFilter, ElementFilterException


class ImageProcessor(ElementFilter):
    """
    Generate a couple of pre-sized images and place them in the cache.
    """
    def __init__(self, obj):
        super(ImageProcessor, self).__init__(obj)

    def process(self, obj, key, valDict, *sizes):

        # Sanity check
        if len(sizes) == 0:
            raise ElementFilterException("ImageProcessor needs at least one image size to process")

        # Do we have an attribute to process?
        if key in valDict and valDict[key]['value']:
            #TODO: Check if a cache entry exists...
            #      ... and if it's new enough

            # Obviously we want to do scaling
            print "-"*80
            print "Object:", obj.uuid
            print "Last changed:", obj.modifyTimestamp
            print "Image processor sizes:", list(sizes)
            print key

            # Convert all images to all requested sizes
            for idx in range(0, len(valDict[key]['value'])):
                image = StringIO.StringIO(valDict[key]['value'][idx].get())
                im = Image.open(image)

                for size in sizes:
                    size = int(size)
                    tmp = ImageOps.fit(im, (size, size), Image.ANTIALIAS)
                    tgt = StringIO.StringIO()
                    tmp.save(tgt, "JPEG")

                    #TODO: insert somewhere

        return key, valDict


class LoadDisplayNameState(ElementFilter):
    """
    Detects the state of the autoDisplayName attribute
    """
    def __init__(self, obj):
        super(LoadDisplayNameState, self).__init__(obj)

    def process(self, obj, key, valDict):

        # No displayName set right now
        if not(len(valDict['displayName']['value'])):
            valDict[key]['value'] = [True]
            return key, valDict

        # Check if current displayName value would match the generated one
        # We will then assume that this user wants to auto update his
        # displayName entry.
        displayName = GenerateDisplayName.generateDisplayName(valDict)
        if displayName == valDict['displayName']['value'][0]:
            valDict[key]['value'] = [True]
            return key, valDict

        # No auto displayName
        valDict[key]['value'] = [False]
        return key, valDict


class GenerateDisplayName(ElementFilter):
    """
    An object filter which automatically generates the displayName entry.
    """
    def __init__(self, obj):
        super(GenerateDisplayName, self).__init__(obj)

    def process(self, obj, key, valDict):
        """
        The out-filter that generates the new displayName value
        """
        # Only generate gecos if the the autoGECOS field is True.
        if len(valDict["autoDisplayName"]['value']) and (valDict["autoDisplayName"]['value'][0]):
            gecos = GenerateDisplayName.generateDisplayName(valDict)
            valDict["displayName"]['value'] = [gecos]

        return key, valDict

    @staticmethod
    def generateDisplayName(valDict):
        """
        This method genereates a new displayName value out of the given properties list.
        """

        sn = ""
        givenName = ""

        if len(valDict["sn"]['value']) and (valDict["sn"]['value'][0]):
            sn = valDict["sn"]['value'][0]
        if len(valDict["givenName"]['value']) and (valDict["givenName"]['value'][0]):
            givenName = valDict["givenName"]['value'][0]

        return "%s %s" % (givenName, sn)
