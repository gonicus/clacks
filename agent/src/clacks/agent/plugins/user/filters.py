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

import Image
import ImageOps #@UnresolvedImport
from bson.binary import Binary
from clacks.common import Environment
from clacks.agent.objects.filter import ElementFilter
from clacks.agent.exceptions import ElementFilterException


try:
    from cStringIO import StringIO
except ImportError:
    from StringIO import StringIO


class ImageProcessor(ElementFilter):
    """
    Generate a couple of pre-sized images and place them in the cache.
    """
    def __init__(self, obj):
        super(ImageProcessor, self).__init__(obj)

        # Get mongo cache collection
        env = Environment.getInstance()
        self.db = env.get_mongo_db('clacks')

        # Ensure basic index for the objects
        for index in ['uuid', 'attribute', 'modified']:
            self.db.cache.ensure_index(index)

    def process(self, obj, key, valDict, *sizes):

        # Sanity check
        if len(sizes) == 0:
            raise ElementFilterException("ImageProcessor needs at least one image size to process")

        # Do we have an attribute to process?
        if key in valDict and valDict[key]['value']:

            # Check if a cache entry exists...
            entry = self.db.cache.find_one({'uuid': obj.uuid, 'attribute': key}, {'modified': 1})
            if entry:

                # Nothing to do if it's unmodified
                if obj.modifyTimestamp == entry['modified']:
                    return key, valDict

            # Create new cache entry
            else:
                c_entry = {
                    'uuid': obj.uuid,
                    'attribute': key
                    }
                self.db.cache.save(c_entry)

            # Convert all images to all requested sizes
            data = {
                    'uuid': obj.uuid,
                    'attribute': key,
                    'modified': obj.modifyTimestamp
                    }
            for idx in range(0, len(valDict[key]['value'])):
                image = StringIO(valDict[key]['value'][idx].get())
                try:
                    im = Image.open(image) #@UndefinedVariable
                except IOError:
                    continue

                for size in sizes:
                    s = int(size)
                    tmp = ImageOps.fit(im, (s, s), Image.ANTIALIAS) #@UndefinedVariable
                    tgt = StringIO()
                    tmp.save(tgt, "JPEG")

                    # Collect all images in [size][] lists
                    if not size in data:
                        data[size] = []

                    data[size].append(Binary(tgt.getvalue()))

            # Update cache
            self.db.cache.update({'uuid': obj.uuid, 'attribute': key}, data)

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
