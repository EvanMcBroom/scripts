#!/usr/bin/env python3
# -*- coding: utf-8 -*-

'''URL encoding and decoding.'''

__all__ = [
    'code', 'encode', 'decode', 'main'
]

import sys
import urllib.parse

def code(func, url):
    '''Tranform the the path portion of a URL using the provided function.

    :param func: The transform to preform
    :type func: function
    :param url: A URL to encode
    :type url: str
    :return: The transformed URL
    :rtype: str
    '''
    parts = urllib.parse.urlsplit(url)
    return urllib.parse.urlunsplit(parts._replace(path = func(parts.path)))

def encode(url):
    '''Encodes the path portion of a URL using the %xx escape.

    :param url: A URL to encode
    :type url: str
    :return: The encoded URL
    :rtype: str
    '''
    return code(urllib.parse.quote_plus, url)

def decode(url):
    '''Replace %xx escapes in the path portion of a URL with their single-character equivalent.

    :param url: A URL to encode
    :type url: str
    :return: The decoded URL
    :rtype: str
    '''
    return code(urllib.parse.unquote_plus, url)

def get_urls(files):
    '''Generate a list or URLs from a list of input files or stdin if no files are given.

    :param files: A list of files
    :type files: list
    :return: A yielded URL
    :rtype: str
    '''
    if len(files) == 0:
        for line in sys.stdin:
            yield line.strip()
    else:
        for file in files:
            with open(file) as _:
                yield from _.readlines()

def main():
    import argparse

    parser = argparse.ArgumentParser(description='URL encode or decode file(s) or standard input')
    parser.add_argument('-d', '--decode', action='store_true', help='Decode the given URLs')
    parser.add_argument('file', nargs='*', help='A file with URLs, one per line')
    args = parser.parse_args()
    for url in get_urls(args.file):
        url = decode(url) if args.decode else encode(url)
        sys.stdout.write(''.join(url.split()) + '\n')

if __name__ == '__main__':
    try:
        main()
    except BrokenPipeError as _:
        sys.exit(_.errno)
    except KeyboardInterrupt as _:
        print()