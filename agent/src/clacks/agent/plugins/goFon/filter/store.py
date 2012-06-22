# -*- coding: utf-8 -*-
from clacks.agent.objects.filter import ElementFilter
from clacks.agent.plugins.goFon.filter.table_defs import sip_users_table, extensions_table, voicemail_users_table
from sqlalchemy.sql import select, delete, and_
from clacks.common.components import PluginRegistry

class storeGoFonAccountSettings(ElementFilter):
    """
    Creates a result-set for the DBMAP backend to store goFon
    settings the the realtime extension tables.
    """
    def __init__(self, obj):
        super(storeGoFonAccountSettings, self).__init__(obj)

    def process(self, obj, key, valDict):
        """
        Detects what password-method was used to generate this hash.
        """

        index = PluginRegistry.getInstance("ObjectIndex")
        actions=[]
        delimiter = "|"

        # Extract required attribute values.
        uid = valDict["uid"]["value"][0]
        phone_numbers = valDict["telephoneNumber"]["value"]
        pin = valDict["goFonPIN"]["value"][0] if len(valDict["goFonPIN"]["value"]) else None
        voicemail_pin = valDict["goFonVoicemailPIN"]["value"][0] if len(valDict["goFonVoicemailPIN"]["value"]) else None
        voicemail_context = valDict["voicemailContext"]["value"][0]
        sip_context = valDict["sipContext"]["value"][0]
        hardware = valDict["goFonHardware"]["value"][0]
        primary_number = phone_numbers[0]
        cn_name = valDict["sn"]["value"][0] + " " + valDict["givenName"]["value"][0]
        mail = valDict["mail"]["value"][0] if "mail" in valDict and len(valDict["mail"]["value"]) else ""
        macro = valDict["goFonMacro"]["value"][0] if len(valDict["goFonMacro"]["value"]) else None
        parameters = "test"

        # Read phone-hardware settings from the index
        res = index.xquery("collection('objects')/o:goFonHardware/o:Attributes[o:cn = '%s']/o:goFonDmtfMode/string()" % hardware)
        dtmf_mode = res[0] in len(res) and res[0] else "rfc2833"
        res = index.xquery("collection('objects')/o:goFonHardware/o:Attributes[o:cn = '%s']/o:goFonQualify/string()" % hardware)
        qualify = res[0] in len(res) and res[0] else "yes"
        res = index.xquery("collection('objects')/o:goFonHardware/o:Attributes[o:cn = '%s']/o:goFonType/string()" % hardware)
        hardware_type = res[0] in len(res) and res[0] else "friend"
        res = index.xquery("collection('objects')/o:goFonHardware/o:Attributes[o:cn = '%s']/o:goFonType/string()" % hardware)
        hardware_type = res[0] in len(res) and res[0] else "friend"

        # Set the ip to to the goFonDefaultIP of the goFonHardware if it is set.
        res = index.xquery("collection('objects')/o:goFonHardware/o:Attributes[o:cn = '%s']/o:goFonDefaultIP/string()" % hardware)
        hardware_ip = res[0] in len(res) and res[0] != "dynamic" else None

        # Query for the used callerid of the given uid, to be able to remove its voicemail entries
        callerid_s = select([sip_users_table.c.callerid]).where(sip_users_table.c.name == uid)
        actions.append(voicemail_users_table.delete().where(voicemail_users_table.c.customer_id == callerid_s))

        # Remove sip_users and enxtensions entries
        actions.append(sip_users_table.delete().where(sip_users_table.c.name == uid))
        actions.append(extensions_table.delete().where(extensions_table.c.exten == uid))

        # Delete old used phone numbers from the extension
        for item in valDict["telephoneNumber"]["in_value"]:
            actions.append(extensions_table.delete().where(extensions_table.c.exten == item))

        # Delete phone numbers from the extension
        for item in valDict["telephoneNumber"]["value"]:
            actions.append(extensions_table.delete().where(extensions_table.c.exten == item))

        #TODO: If the goFonHomeServer has changed, then try to remove the entries from the old server..

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
        actions.append(sip_users_table.insert().values(**sip_entry))

        # Create the voicemail entry
        voice_entry = {}
        voice_entry["customer_id"] = primary_number
        voice_entry["mailbox"]     = primary_number
        voice_entry["password"]    = voicemail_pin
        voice_entry["fullname"]    = cn_name
        voice_entry["context"]     = voicemail_context
        voice_entry["email"]       = mail
        actions.append(voicemail_users_table.insert().values(**voice_entry))

        # Create extensions entries (uid -> number)
        ext_entry = {}
        ext_entry['context'] = 'GOsa';
        ext_entry['exten']   = uid
        ext_entry['priority']= 1;
        ext_entry['app']     = "Goto";
        ext_entry['appdata'] = primary_number + delimiter + "1"
        actions.append(extensions_table.insert().values(**ext_entry))

        # Create extensions entries (primary -> number)
        ext_entry = {}
        ext_entry['context'] = 'GOsa';
        ext_entry['exten']   = primary_number
        ext_entry['priority']= 0;
        ext_entry['app']     = 'SIP/' + uid
        actions.append(extensions_table.insert().values(**ext_entry))

        # Set macro if one is selected
        if macro:
            s_app = "Macro"
            s_par = macro + delimiter + macro_parameter
        else:
            s_app = "Dial"
            s_par = 'SIP/' + uid + delimiter + str(20) + delimiter + "r"

        # Create extensions entries (secondary -> number)
        for item in valDict["telephoneNumber"]["in_value"]:
            ext_entry['context'] = 'GOsa'
            ext_entry['exten']   = item
            ext_entry['priority']= 1
            ext_entry['app']     = s_app
            ext_entry['appdata'] = s_par
            actions.append(extensions_table.insert().values(**ext_entry))

        valDict[key]["value"] = actions
        return key, valDict
