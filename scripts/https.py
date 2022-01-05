#!/usr/bin/env python3
# -*- coding: utf-8 -*-

'''HTTPs server classes.'''

__all__ = [
    'HTTPSServer', 'ThreadingHTTPSServer', 'main'
]

import OpenSSL
import http.server
import socket
import socketserver
import ssl
import sys
import tempfile

class HTTPSServer(http.server.HTTPServer):
    allow_reuse_address = 1

    def __init__(self, *args, **kwargs):
        keyfile = kwargs['keyfile']
        certfile = kwargs['certfile']
        del kwargs['keyfile']
        del kwargs['certfile']
        super().__init__(*args, **kwargs)
        self.socket = ssl.wrap_socket(self.socket, server_side=True, keyfile=keyfile, certfile=certfile, ssl_version=ssl.PROTOCOL_TLS)

class ThreadingHTTPSServer(socketserver.ThreadingMixIn, HTTPSServer):
    daemon_threads = True

def generate_key():
    '''Creates an RSA key pair.

    :return: Path to an RSA private key. The public key will have a .pub extension
    :rtype: str
    '''
    key = OpenSSL.crypto.PKey()
    key.generate_key(OpenSSL.crypto.TYPE_RSA, 4096)
    keyFile = tempfile.mktemp()
    with open(keyFile, 'wb') as file:
        file.write(OpenSSL.crypto.dump_privatekey(OpenSSL.crypto.FILETYPE_PEM, key))
    with open('{}.pub'.format(keyFile), 'wb') as file:
        file.write(OpenSSL.crypto.dump_publickey(OpenSSL.crypto.FILETYPE_PEM, key))
    return keyFile

def generate_cert(keyfile, expiration=12*365*24*60*60):
    '''Creates a key and self-signed cert.

    :param keyfile: Path to an RSA private key
    :type keyfile: str
    :param expiration: how long the cert is valid in seconds, defaults to one year
    :type expiration: int, optional
    :return: PEM formatted X509 cert
    :rtype: class:`simpleble.SimpleBleClient`
    '''
    # Create a cert
    cert = OpenSSL.crypto.X509()
    cert.gmtime_adj_notBefore(0)
    cert.gmtime_adj_notAfter(expiration)
    # Self-sign and write the cert to a temporary file
    with open('{}.pub'.format(keyfile), 'rb') as file:
        cert.set_pubkey(OpenSSL.crypto.load_publickey(OpenSSL.crypto.FILETYPE_PEM, file.read()))
    with open(keyfile, 'rb') as file:
        cert.sign(OpenSSL.crypto.load_privatekey(OpenSSL.crypto.FILETYPE_PEM, file.read()), 'sha512')
    certFile = tempfile.mktemp()
    with open(certFile, 'wb') as file:
        file.write(OpenSSL.crypto.dump_certificate(OpenSSL.crypto.FILETYPE_PEM, cert))
    return certFile

# modified from: cpython/blob/3.10/Lib/http/server.py
def test(HandlerClass=http.server.BaseHTTPRequestHandler, ServerClass=ThreadingHTTPSServer, protocol='HTTP/1.0', port=8443, bind=None):
    '''Test the HTTP request handler class wrapped with TLS.
    This runs an HTTPS server on port 8443 (or the port argument).

    :param HandlerClass: HTTP request handler to use
    :type HandlerClass: class:`http.server.BaseHTTPRequestHandler`, optional
    :param ServerClass: HTTPS server class to use
    :type ServerClass: class:`http.server.HTTPSServer`, optional
    :param protocol: HTTP protocol to use (e.g. HTTP/1.0 or HTTP/1.1)
    :type protocol: str, optional
    :param port: Port to bind to
    :type port: int, optional
    :param bind: Host address to bind to
    :type bind: str, optional
    '''
    # Get the best family
    infos = socket.getaddrinfo(bind, port, type=socket.SOCK_STREAM, flags=socket.AI_PASSIVE)
    ServerClass.address_family, type, proto, canonname, sockaddr = next(iter(infos))
    # Start the server
    HandlerClass.protocol_version = protocol
    with ServerClass(sockaddr, HandlerClass) as httpd:
        host, port = httpd.socket.getsockname()[:2]
        url_host = f'[{host}]' if ':' in host else host
        print(f'Serving HTTPS on {host} port {port} (https://{url_host}:{port}/) ...')
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print('\nKeyboard interrupt received, exiting.')
            sys.exit(0)

# modified from: cpython/blob/3.10/Lib/http/server.py
def main():
    import argparse
    import contextlib
    import functools
    import socket
    import os

    parser = argparse.ArgumentParser(description='Start an HTTPs server.')
    parser.add_argument('--cgi', action='store_true', help='Run as CGI Server')
    parser.add_argument('--bind', '-b', metavar='ADDRESS', help='Specify alternate bind address [default: all interfaces]')
    parser.add_argument('--directory', '-d', default=os.getcwd(), help='Specify alternative directory [default:current directory]')
    parser.add_argument('--key', '-k', help='Private key [default:auto generated]')
    parser.add_argument('--cert', '-c', help='Specify cert [default:self signed]')
    parser.add_argument('port', action='store', default=8443, type=int, nargs='?', help='Specify alternate port [default: 8443]')
    args = parser.parse_args()
    if args.cgi:
        handler_class = http.server.CGIHTTPRequestHandler
    else:
        handler_class = functools.partial(http.server.SimpleHTTPRequestHandler, directory=args.directory)
    keyfile, certfile = (args.key, args.cert)
    
    # Ensure dual-stack is not disabled; ref #38907
    class DualStackServer(ThreadingHTTPSServer):
        def __init__(self, *args, **kwargs):
            kwargs['keyfile'] = keyfile
            kwargs['certfile'] = certfile
            super().__init__(*args, **kwargs)

        def server_bind(self):
            # Suppress exception when protocol is IPv4
            with contextlib.suppress(Exception):
                self.socket.setsockopt(socket.IPPROTO_IPV6, socket.IPV6_V6ONLY, 0)
            return super().server_bind()

    try:
        if not (args.key and args.cert):
            keyfile = generate_key()
            certfile = generate_cert(keyfile)
            for path in [keyfile, '{}.pub'.format(keyfile), certfile]:
                with open(path) as file:
                    print(file.read())

            test(HandlerClass=handler_class, ServerClass=DualStackServer, port=args.port, bind=args.bind)
    finally:
        if not (args.key and args.cert):
            for path in [keyfile, '{}.pub'.format(keyfile), certfile]:
                if os.path.isfile(path):
                    os.unlink(path)

if __name__ == '__main__':
    main()