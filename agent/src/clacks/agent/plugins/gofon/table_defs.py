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

from sqlalchemy import Table, Column, Integer, String, MetaData, DateTime, Enum

metadata = MetaData()

extensions_table = Table("extensions", metadata,
   Column("id", Integer(11), primary_key=True),
   Column("context", String(20), nullable=False, default='', primary_key=True),
   Column("exten", String(20), nullable=False, default='', primary_key=True),
   Column("priority", Integer(4), nullable=False, default='0', primary_key=True),
   Column("app", String(20), nullable=False, default=''),
   Column("appdata", String(128), nullable=False, default='')
)

queue_members_table = Table("queue_members", metadata,
  Column("uniqueid", Integer(10), nullable=False, primary_key=True),
  Column("membername", String(40), default=None),
  Column("queue_name", String(128), default=None, unique=True),
  Column("interface", String(128), default=None, unique=True),
  Column("penalty", Integer(11), default=None),
  Column("paused", Integer(1), default=None)
)

queues_table = Table("queues", metadata,
  Column("name", String(128), nullable=False),
  Column("musiconhold", String(128), default=None),
  Column("announce", String(128), default=None),
  Column("context", String(128), default=None),
  Column("timeout", Integer(11), default=None),
  Column("monitor_join", Integer(1), default=None),
  Column("monitor_format", String(128), default=None),
  Column("queue_youarenext", String(128), default=None),
  Column("queue_thereare", String(128), default=None),
  Column("queue_callswaiting", String(128), default=None),
  Column("queue_holdtime", String(128), default=None),
  Column("queue_minutes", String(128), default=None),
  Column("queue_seconds", String(128), default=None),
  Column("queue_lessthan", String(128), default=None),
  Column("queue_thankyou", String(128), default=None),
  Column("queue_reporthold", String(128), default=None),
  Column("announce_frequency", Integer(11), default=None),
  Column("announce_round_seconds", Integer(11), default=None),
  Column("announce_holdtime", String(128), default=None),
  Column("retry", Integer(11), default=None),
  Column("wrapuptime", Integer(11), default=None),
  Column("maxlen", Integer(11), default=None),
  Column("servicelevel", Integer(11), default=None),
  Column("strategy", String(128), default=None),
  Column("joinempty", String(128), default=None),
  Column("leavewhenempty", String(128), default=None),
  Column("eventmemberstatus", Integer(1), default=None),
  Column("eventwhencalled", Integer(1), default=None),
  Column("reportholdtime", Integer(1), default=None),
  Column("memberdelay", Integer(11), default=None),
  Column("weight", Integer(11), default=None),
  Column("timeoutrestart", Integer(1), default=None),
  Column("periodic_announce", String(50), default=None),
  Column("periodic_announce_frequency", Integer(11), default=None)
)

sip_users_table = Table("sip_users", metadata,
  Column("id", Integer(11), nullable=False, primary_key=True),
  Column("name", String(80), nullable=False, default='', unique=True),
  Column("host", String(31), nullable=False, default=''),
  Column("nat", String(5), nullable=False, default='no'),
  Column("type", Enum('user', 'peer', 'friend'), nullable=False, default='friend'),
  Column("accountcode", String(20), default=None),
  Column("amaflags", String(13), default=None),
  Column("callgroup", String(10), default=None),
  Column("callerid", String(80), default=None),
  Column("cancallforward", String(3), default='yes'),
  Column("canreinvite", String(3), default='yes'),
  Column("context", String(80), default=None),
  Column("defaultip", String(15), default=None),
  Column("dtmfmode", String(7), default=None),
  Column("fromuser", String(80), default=None),
  Column("fromdomain", String(80), default=None),
  Column("insecure", String(4), default=None),
  Column("language", String(2), default=None),
  Column("mailbox", String(50), default=None),
  Column("md5secret", String(80), default=None),
  Column("deny", String(95), default=None),
  Column("permit", String(95), default=None),
  Column("mask", String(95), default=None),
  Column("musiconhold", String(100), default=None),
  Column("pickupgroup", String(10), default=None),
  Column("qualify", String(3), default=None),
  Column("regexten", String(80), default=None),
  Column("restrictcid", String(3), default=None),
  Column("rtptimeout", String(3), default=None),
  Column("rtpholdtimeout", String(3), default=None),
  Column("secret", String(80), default=None),
  Column("setvar", String(100), default=None),
  Column("disallow", String(100), default='all'),
  Column("allow", String(100), default='g729;ilbc;gsm;ulaw;alaw'),
  Column("fullcontact", String(80), nullable=False, default=''),
  Column("ipaddr", String(15), nullable=False, default=''),
  Column("port", Integer(5), nullable=False, default='0'),
  Column("regserver", String(100), default=None),
  Column("regseconds", Integer(11), nullable=False, default='0'),
  Column("username", String(80), nullable=False, default='')
)

voicemail_users_table = Table("voicemail_users", metadata,
  Column("uniqueid", Integer(11), nullable=False, primary_key=True),
  Column("customer_id", String(11), nullable=False, default='0'),
  Column("context", String(50), nullable=False, default=''),
  Column("mailbox", String(11), nullable=False, default='0'),
  Column("password", String(5), nullable=False, default='0'),
  Column("fullname", String(150), nullable=False, default=''),
  Column("email", String(50), nullable=False, default=''),
  Column("pager", String(50), nullable=False, default=''),
  Column("tz", String(10), nullable=False, default='central'),
  Column("attach", String(4), nullable=False, default='yes'),
  Column("saycid", String(4), nullable=False, default='yes'),
  Column("dialout", String(10), nullable=False, default=''),
  Column("callback", String(10), nullable=False, default=''),
  Column("review", String(4), nullable=False, default='no'),
  Column("operator", String(4), nullable=False, default='no'),
  Column("envelope", String(4), nullable=False, default='no'),
  Column("sayduration", String(4), nullable=False, default='no'),
  Column("saydurationm", Integer(4), nullable=False, default='1'),
  Column("sendvoicemail", String(4), nullable=False, default='no'),
  Column("delete", String(4), 	nullable=False, default='no'),
  Column("nextaftercmd", String(4), nullable=False, default='yes'),
  Column("forcename", String(4), nullable=False, default='no'),
  Column("forcegreetings", String(4), nullable=False, default='no'),
  Column("hidefromdir", String(4), nullable=False, default='yes'),
  Column("stamp", DateTime, nullable=False)
)
