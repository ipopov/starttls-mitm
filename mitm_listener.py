#!/usr/bin/env python

import sys, socket, thread, ssl
from select import select

HOST = '0.0.0.0'
PORT = 5222
BUFSIZE = 4096

def wrap_sockets(client_sock, server_sock, certfile, keyfile):
  return (ssl.wrap_socket(client_sock,
              server_side=True,
              suppress_ragged_eofs=True,
              certfile=certfile,
              keyfile=keyfile),
          ssl.wrap_socket(
              server_sock,
              suppress_ragged_eofs=True))


def do_relay(client_sock, server_sock, certfile, keyfile):
  server_sock.settimeout(1.0)   
  client_sock.settimeout(1.0)
  print 'RELAYING'
  while 1:
    try:
      # Peek for the beginnings of an ssl handshake
      try:
        maybe_handshake = client_sock.recv(
            BUFSIZE, socket.MSG_PEEK | socket.MSG_DONTWAIT)
        if maybe_handshake.startswith('\x16\x03'):
          print 'Wrapping sockets.'
          client_sock, server_sock = wrap_sockets(client_sock,
              server_sock, certfile, keyfile)
      except:
        # For some reason, MSG_PEEK fails when applied to an SSL
        # socket
        pass
      receiving, _, _ = select([client_sock, server_sock], [], [])
      if client_sock in receiving:
        p = client_sock.recv(BUFSIZE)
        print "C->S", len(p), repr(p)
        server_sock.send(p)

      if server_sock in receiving:
        p = server_sock.recv(BUFSIZE)
        print "S->C", len(p), repr(p)
        client_sock.send(p)
    except socket.error as e:
      if "timed out" not in str(e):
        raise e


# Relay information, peeking at the data on every read for an SSL
# handshake header. Assume that the _client_ initiates the
# handshaking, so it's safe to just peek at the client's packets.
#
# When the client initiates a handshake, assume that the server has no
# data left to send. (This assumption works for XMPP starttls but
# probably not for other protocols.)
def child(clientsock,target,certfile,keyfile):
  targetsock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
  targetsock.connect((target,PORT))

  do_relay(clientsock, targetsock, certfile, keyfile)

if __name__=='__main__': 
  if len(sys.argv) < 4:
    sys.exit('Usage: %s TARGETHOST <KEYFILE> <CERTFILE>\n' % sys.argv[0])
  target = sys.argv[1]
  keyfile = sys.argv[2]
  certfile = sys.argv[3]
  myserver = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
  myserver.bind((HOST, PORT))
  myserver.listen(2)
  print 'LISTENER ready on port', PORT
  while 1:
    client, addr = myserver.accept()
    print 'CLIENT CONNECT from:', addr
    thread.start_new_thread(child, (client,target,certfile,keyfile))
