dn=%[generate_unique_dn(%(base)s, %(cn)s, %(givenName)s)]f
cn=%(givenName)s %(sn)s
uid=%[generate_unique_uid(%(sn)s, %(givenName)s)]f
