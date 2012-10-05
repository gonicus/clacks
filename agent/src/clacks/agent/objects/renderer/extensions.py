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

from clacks.agent.objects.renderer import ResultRenderer


class ExtensionRenderer(ResultRenderer):

    @staticmethod
    def getName():
        return "extensions"

    @staticmethod
    def render(data):
        if "Extension" in data:
            return "Extensions: " + (", ".join(["<a href='clacks://%s/%s?edit'>%s</a>" % (data['DN'][0], i, i) for i in data['Extension']]))

        return ""
