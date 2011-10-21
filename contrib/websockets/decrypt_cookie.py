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

    print [signature,expires,content]


auth("7v8bsXUEVJ9ddJrvzG8nM5SN_HcyMDExMTAyMjE4NTJSRU1PVEVfVVNFUj1jYWp1cztSRU1PVEVfU0VTU0lPTj03ZjRlZThkMi1mYmUzLTExZTAtYjM0NS01NDUyMDA1ZjEyNTA~")
