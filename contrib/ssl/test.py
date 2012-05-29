import sys
from OpenSSL.crypto import PKCS12, load_certificate, FILETYPE_PEM

if sys.version_info < (3, 0):
    def b(s):
        return s
    bytes = str
else:
    def b(s):
        return s.encode("charmap")
    bytes = bytes

cleartextCertificatePEM = b("""-----BEGIN CERTIFICATE-----
MIIFGzCCBISgAwIBAgICAIwwDQYJKoZIhvcNAQEFBQAwgYMxCzAJBgNVBAYTAkRF
MQwwCgYDVQQIEwNOUlcxETAPBgNVBAcTCEFybnNiZXJnMRUwEwYDVQQKEwxHT05J
Q1VTIEdtYkgxEzARBgNVBAMTCkdPTklDVVMgQ0ExJzAlBgkqhkiG9w0BCQEWGGNl
cnRpZmljYXRpb25AR09OSUNVUy5kZTAeFw0xMjA1MjkxMDE1MDhaFw0xMzA1Mjkx
MDE1MDhaMFYxCzAJBgNVBAYTAkRFMQwwCgYDVQQIEwNOUlcxETAPBgNVBAcTCEFy
bnNiZXJnMRUwEwYDVQQKEwxHT05JQ1VTIEdtYkgxDzANBgNVBAMTBnB5VGVzdDCC
AiIwDQYJKoZIhvcNAQEBBQADggIPADCCAgoCggIBAMzagUUqIqWDZgEFQyg2DTom
BfkqFnlD456l02zFIC8sPM0d+VddXKT8Fw+VMvpJqHqUI5vXgQXTGLXQ46nm+jkm
x5APX6vzJkd/x2O3J8Np50HdJh+PizlRD9f4EgIWYuvkxOCVh3KW9TSv1kACBe/8
ATtLtFvwp1V4sjLPXAaBknt0F/ztdzFtaPtlVRYTkWuF+gGnk0jSthmqVjLLV+I+
eFS6g2P3dXWfQBWa23KSvjeaPdRMwsOeFsL2TouDB+25avqI0GhrvnTTibNEGE7j
yv5wNffbiSEPbBfiU2f42tRMcbSLYOFYcXBAz6Mred+iscLytGkXhg0tS342tphY
a/NwnJ6EcxZWHucSTFXzTD1Ore3LmVX3oEucR4KsxaXlXcdvRTCwtnvZVM2q3MPZ
r2HrXYSmI/F2WmOcyTTRF+TvqiJlsns9JnkFHtrKbNA8MTHvmEM+66hu0AiDR2Lh
p2iuGCcqPMiqhDX/YFFV0equgEM9FqaRalPudVCem8zfcMpjms2k1v/C2hM9Q7IF
FeiT+ciYOkP+HCLAvC1MgCjnbSpyXlJa4txc9ayC3Ye3IAskhVpjLCyJcjnsFhe5
hF6Rk97a4Gx9c01olLTHkmM+xgEGAfNHReyJ2zwOQc4SC1LghqKFTHH0eDtnCbDI
TnRaNyfF7lxFaXFpRRFbAgMBAAGjggFEMIIBQDAJBgNVHRMEAjAAMBEGCWCGSAGG
+EIBAQQEAwIEsDArBglghkgBhvhCAQ0EHhYcVGlueUNBIEdlbmVyYXRlZCBDZXJ0
aWZpY2F0ZTAdBgNVHQ4EFgQUEzXyLNlcs/a8eYTo8eY32+vCbnIwgbAGA1UdIwSB
qDCBpYAUV6dlWu1HzF9/P6PbRwV97Bp2J7uhgYmkgYYwgYMxCzAJBgNVBAYTAkRF
MQwwCgYDVQQIEwNOUlcxETAPBgNVBAcTCEFybnNiZXJnMRUwEwYDVQQKEwxHT05J
Q1VTIEdtYkgxEzARBgNVBAMTCkdPTklDVVMgQ0ExJzAlBgkqhkiG9w0BCQEWGGNl
cnRpZmljYXRpb25AR09OSUNVUy5kZYIBADAJBgNVHRIEAjAAMAkGA1UdEQQCMAAw
CwYDVR0PBAQDAgWgMA0GCSqGSIb3DQEBBQUAA4GBACYa0fqx4ueHELEbtbJd1GeL
qeBgaBnOUNnTaEb1P+mNup+0J9u8sdIb3sAtKUFecyxFjtWFmk6tRi+5aBmLMtsW
abEXiH/4TdlAQr3eAPGHuihkWgDUloEvbpSJa3PyEuBxRk6ThQ1wLDS60pgm+KKz
/e3Xzuly7AWbsus5Eh4q
-----END CERTIFICATE-----
""")


p12 = PKCS12()
cert = load_certificate(FILETYPE_PEM, cleartextCertificatePEM)
p12.set_certificate(cert)
cert = p12.get_certificate()

print "Subject:", cert.get_subject().get_components()
print "Version:", cert.get_version()
print "Issuer:", cert.get_issuer().get_components()
print "Start:", cert.get_notBefore()
print "End:", cert.get_notAfter()
print "Serial:", cert.get_serial_number()
print "Algorithm:", cert.get_signature_algorithm()

print "Extensions:"
for ext in range(0, cert.get_extension_count()):
    print cert.get_extension(ext)

