# -*- coding: utf-8 -*-
import hmac, base64, random, time, warnings
from hashlib import sha1

def make_time(value):
    return time.strftime("%Y%m%d%H%M", time.gmtime(value))


def auth(cookie):
    decode = base64.decodestring(cookie.replace("_", "/").replace("~", "="))
    _signature_size = len(hmac.new('x', 'x', sha1).digest())
    _header_size = _signature_size + len(make_time(time.time()))

    signature = decode[:_signature_size]
    expires = decode[_signature_size:_header_size]
    content = decode[_header_size:]

    if signature == hmac.new("TecloigJink4", content, sha1).digest():
        if int(expires) > int(make_time(time.time())):
            return content
        else:
            # This is the normal case of an expired cookie; just
            # don't bother doing anything here.
            raise(Exception("Nö du darfst nicht! Abgelaufen"));
    else:
        # This case can happen if the server is restarted with a
        # different secret; or if the user's IP address changed
        # due to a proxy.  However, it could also be a break-in
        # attempt -- so should it be reported?
        raise(Exception("Nö du darfst nicht! Signatur falsch"));


c_str = "7v8bsXUEVJ9ddJrvzG8nM5SN_HcyMDExMTAyMjE4NTJSRU1PVEVfVVNFUj1jYWp1cztSRU1PVEVfU0VTU0lPTj03ZjRlZThkMi1mYmUzLTExZTAtYjM0NS01NDUyMDA1ZjEyNTA~"


if(auth(c_str)):
    print "Geht klar"
