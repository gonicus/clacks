dn=TolleYeah%generate_unique_dn(%(base)s, %(cn)s, %(givenName)s)f
sn=%generate_unique_name()f
givenName=%generate_unique_name()f
cn=hallo%(givenName)s das %(sn)s is toll
uid=%generate_unique_uid(%(sn)s, Schnitte, %(givenName)s)f
