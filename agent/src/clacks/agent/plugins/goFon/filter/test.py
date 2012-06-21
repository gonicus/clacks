from table_defs import sip_users_table
from sqlalchemy.sql import and_



print sip_users_table.select(and_(sip_users_table.c.name == "test", sip_users_table.c.name == "asdf"))
