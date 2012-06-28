# -*- coding: utf-8 -*-
from clacks.common.components import PluginRegistry, Plugin
from clacks.common.components.command import Command
from clacks.common.utils import N_
from zope.interface import implements
from clacks.common.handler import IInterfaceHandler
from clacks.common.components import PluginRegistry
from clacks.agent.plugins.gofon.filter.table_defs import sip_users_table, extensions_table, voicemail_users_table
from sqlalchemy.sql import select, delete, and_
from clacks.agent.objects.backend import ObjectBackend
from sqlalchemy import create_engine, Table, Column, Integer, String, MetaData, BLOB, DateTime
from clacks.common import Environment
from logging import getLogger


class goFonAccount(Plugin):
    """
    Test
    """
    implements(IInterfaceHandler)

    _priority_ = 12
    _target_ = 'gofon'

    env = None
    log = None

    def serve(self):
        self.env = Environment.getInstance()
        self.log = getLogger(__name__)

    @Command(__help__=N_("Remove the goFon extensions for a given user (uuid)"))
    def removeGoFonAccount(self, uuid):
        s_wrapper = PluginRegistry.getInstance("SearchWrapper")
        s_index = PluginRegistry.getInstance("ObjectIndex")
        query = """
        SELECT User.*
        BASE User SUB "dc=example,dc=net"
        WHERE User.UUID = "%s"
        ORDER BY User.UUID
        """ % (uuid)

        result = s_wrapper.execute(query)
        if result and len(result) == 1:

            # Extract required attribute values.
            entry = result[0]["User"]

            # Nothing to do here, no account found...
            if "goFonHomeServer" not in entry:
                return
            else:

                uid = entry["uid"][0]
                home_server = entry["goFonHomeServer"][0]
                phone_numbers = entry["telephoneNumber"]


                # Remove entries from the old home server
                actions = {}
                actions[home_server] = []

                # Query for the used callerid of the given uid, to be able to remove its voicemail entries
                callerid_s = select([sip_users_table.c.callerid]).where(sip_users_table.c.name == uid)
                actions[home_server].append(voicemail_users_table.delete().where(voicemail_users_table.c.customer_id == callerid_s))

                # Remove sip_users and enxtensions entries
                actions[home_server].append(sip_users_table.delete().where(sip_users_table.c.name == uid))
                actions[home_server].append(extensions_table.delete().where(extensions_table.c.exten == uid))

                # Delete old used phone numbers from the extension
                for item in phone_numbers:
                    actions[home_server].append(extensions_table.delete().where(extensions_table.c.exten == item))

                self.execute_actions(actions)

    @Command(__help__=N_("Adds a goFon extension for a given user (uuid)"))
    def storeGoFonAccount(self, uuid):

        s_wrapper = PluginRegistry.getInstance("SearchWrapper")
        index = PluginRegistry.getInstance("ObjectIndex")
        query = """
        SELECT User.*
        BASE User SUB "dc=example,dc=net"
        WHERE User.UUID = "%s"
        ORDER BY User.UUID
        """ % (uuid)
        result = s_wrapper.execute(query)
        if result and len(result) == 1:
            entry = result[0]["User"]

            # Extract required attribute values.
            uid = entry["uid"][0]
            phone_numbers = entry["telephoneNumber"]
            pin = entry["goFonPIN"][0] if "goFonPIN" in entry else None
            voicemail_pin = entry["goFonVoicemailPIN"][0] if "goFonVoicemailPIN" in entry else None
            hardware = entry["goFonHardware"][0]
            primary_number = phone_numbers[0]
            cn_name = entry["sn"][0] + " " + entry["givenName"][0]
            mail = entry["mail"][0] if "mail" in entry else ""
            macro = entry["goFonMacro"][0] if "goFonMacro" in entry else None
            macro_parameter = "unknown"
            home_server = entry["goFonHomeServer"][0]

            delimiter = self.env.config.get("gofon.delimiter", "|")
            voicemail_context = self.env.config.get("gofon.voicemail_context", None)
            if not voicemail_context:
                raise Exception("please define gofon.voicemail_context in your config!")
            sip_context = self.env.config.get("gofon.sip_context", None)
            if not sip_context:
                raise Exception("please define gofon.sip_context in your config!")

            # Read phone-hardware settings from the index
            res = index.xquery("collection('objects')/o:goFonHardware/o:Attributes[o:cn = '%s']/o:goFonDmtfMode/string()" % hardware)
            dtmf_mode = res[0] if len(res) and res[0] else "rfc2833"
            res = index.xquery("collection('objects')/o:goFonHardware/o:Attributes[o:cn = '%s']/o:goFonQualify/string()" % hardware)
            qualify = res[0] if len(res) and res[0] else "yes"
            res = index.xquery("collection('objects')/o:goFonHardware/o:Attributes[o:cn = '%s']/o:goFonType/string()" % hardware)
            hardware_type = res[0] if len(res) and res[0] else "friend"

            # Now create the new entries
            sip_entry = {}
            sip_entry['dtmfmode']     = dtmf_mode
            sip_entry['callerid']     = primary_number
            sip_entry['name']         = uid
            sip_entry['canreinvite']  = "no"
            sip_entry['context']      = sip_context
            sip_entry['host']         = hardware
            sip_entry['mailbox']      = "%s@%s" % (primary_number, voicemail_context)
            sip_entry['nat']          = "no"
            sip_entry['qualify']      = qualify
            sip_entry['restrictcid']  = "n"
            sip_entry['secret']       = pin
            sip_entry['username']     = uid
            sip_entry['ipaddr']       = hardware
            actions = {home_server: []}
            actions[home_server].append(sip_users_table.insert().values(**sip_entry))

            # Create the voicemail entry
            voice_entry = {}
            voice_entry["customer_id"] = primary_number
            voice_entry["mailbox"]     = primary_number
            voice_entry["password"]    = voicemail_pin
            voice_entry["fullname"]    = cn_name
            voice_entry["context"]     = voicemail_context
            voice_entry["email"]       = mail
            actions[home_server].append(voicemail_users_table.insert().values(**voice_entry))

            # Create extensions entries (uid -> number)
            ext_entry = {}
            ext_entry['context'] = 'GOsa';
            ext_entry['exten']   = uid
            ext_entry['priority']= 1;
            ext_entry['app']     = "Goto";
            ext_entry['appdata'] = primary_number + delimiter + "1"
            actions[home_server].append(extensions_table.insert().values(**ext_entry))

            # Create extensions entries (primary -> number)
            ext_entry = {}
            ext_entry['context'] = 'GOsa';
            ext_entry['exten']   = primary_number
            ext_entry['priority']= 0;
            ext_entry['app']     = 'SIP/' + uid
            actions[home_server].append(extensions_table.insert().values(**ext_entry))

            # Set macro if one is selected
            if macro:
                s_app = "Macro"
                s_par = macro + delimiter + macro_parameter
            else:
                s_app = "Dial"
                s_par = 'SIP/' + uid + delimiter + str(20) + delimiter + "r"

            # Create extensions entries (secondary -> number)
            for item in phone_numbers:
                ext_entry['context'] = 'GOsa'
                ext_entry['exten']   = item
                ext_entry['priority']= 1
                ext_entry['app']     = s_app
                ext_entry['appdata'] = s_par
                actions[home_server].append(extensions_table.insert().values(**ext_entry))
            self.execute_actions(actions)


    def execute_actions(self, data):

        if not self.env:
            raise Exception("no yet ready...")

        # Extract action per connection
        connections = {}
        actions = {}
        for database in data:

            # Try to find a database connection for the DB
            con_str = self.env.config.get("gofon.%s" % (database.replace(".", "_")), None)
            if not con_str:
                raise Exception("no database connection specified for %s! Please add config parameters for %s" % \
                        (database, "gofon.%s" % (database.replace(".", "_"))))

            # Try to establish the connection
            engine = create_engine(con_str)
            if database not in connections:
                connections[database] = engine
                actions[database] = []
            actions[database] += data[database]

        # Execute actions on the database connection, as transaction
        for database in actions:
            with connections[database].begin() as conn:
                for action in actions[database]:
                    try:
                        conn.execute(action)
                        print "*", action
                    except Exception as e:
                        raise Exception("failed to execute SQL statement '%s' on database '%s': %s" % (str(action), database, str(e)))


