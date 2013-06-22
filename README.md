`starttls-mitm` is a mitm proxy that will transparently proxy and dump
both plaintext and TLS traffic. It uses a user-provided keyfile and
certificate file to impersonate remote servers. The user must
explicitly instruct the device being man-in-the-middled to trust this
certificate authority -- so this is not a security compromise.

It starts out relaying in plaintext, peeking at each packet for a
ClientHello header, at which point it converts the sockets to TLS.
