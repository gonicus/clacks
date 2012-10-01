import traceback
import gettext
from datetime import datetime
from pkg_resources import resource_filename #@UnresolvedImport
from bson import ObjectId
from clacks.common.utils import N_
from clacks.common import Environment
from clacks.common.components import Command
from clacks.common.components import Plugin


class ClacksErrorHandler(Plugin):
    #TODO: maintain the owner (or originator) of the error message, to
    #      allow only the originator to pull her/his error messages.
    _target_ = 'core'
    _codes = {}
    _i18n_map = {}

    def __init__(self):
        self.env = Environment.getInstance()
        self.__db = self.env.get_mongo_db('clacks').errors

    @Command(needsUser=True, __help__=N_("Get the error message assigned to a specific ID."))
    def get_error(self, user, _id, locale=None, trace=False):
        res = None

        if trace:
            res = self.__db.find_one({'_id': ObjectId(_id)})
        else:
            res = self.__db.find_one({'_id': ObjectId(_id)}, {'trace': 0})

        # Translate message if requested
        if res and locale:
            mod = ClacksErrorHandler._i18n_map[res['code']]
            t = gettext.translation('messages',
                resource_filename(mod, "locale"),
                fallback=True,
                languages=[locale])

            res['text'] = t.ugettext(ClacksErrorHandler._codes[res['code']])

        # Fill keywords
        res['text'] % res['kwargs']
        res['_id'] = _id

        # Remove the entry
        self.__db.remove({'_id': ObjectId(_id)})

        return res

    @staticmethod
    def make_error(code, topic=None, **kwargs):
        # Convert to real message
        detail = ""

        # Add topic to make it usable inside of the error messages
        if not kwargs:
            kwargs = {}
        kwargs.update(dict(topic=topic))

        # Assemble message
        detail = ClacksErrorHandler._codes[code] % kwargs

        # Write to db and update uuid
        env = Environment.getInstance()
        db = env.get_mongo_db('clacks').errors
        data = dict(code=code, topic=topic, text=detail,
                args=args, kwargs=kwargs, trace=traceback.format_stack(),
                timestamp=datetime.now(), user=None)
        __id = str(db.save(data))

        # First, catch unconverted exceptions
        if not code in ClacksErrorHandler._codes:
            return code

        return '<%s> %s' % (__id, detail)

    @staticmethod
    def register_codes(codes, module="clacks.agent"):
        ClacksErrorHandler._codes.update(codes)

        # Memorize which module to get translations from
        for k in codes.keys():
            ClacksErrorHandler._i18n_map[k] = module
