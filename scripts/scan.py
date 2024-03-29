#!/usr/bin/env python3
# -*- coding: utf-8 -*-

'''File, directory, and archive scanning.'''

__all__ = [
    'archive', 'directory', 'file', 'main', 'open_uncompressed'
]

import bz2, gzip, lzma
import mimetypes
import os
import re
from rich.console import Console
from rich.table import Column, Table
import tarfile, zipfile
import tempfile

# Do not include a regex for URLs because it causes too many duplicates with email, domain_name, ipv4_address, and ipv6_address
identifiers = {
    # https://www.regular-expressions.info/email.html
    'email': r'[a-z0-9!#$%&\'*+/=?^_‘{|}~-]+(?:\.[a-z0-9!#$%&\'*+/=?^_‘{|}~-]+)*@(?:[a-z0-9](?:[a-z0-9-]*[a-z0-9])?\.)+[a-z0-9](?:[a-z0-9-]*[a-z0-9])?',
    # https://stackoverflow.com/a/26987741/11039217
    'domain_name': r'(((?!\-))(xn\-\-)?[a-z0-9\-_]{0,61}[a-z0-9]{1,1}\.)*(xn\-\-)?([a-z0-9\-]{1,61}|[a-z0-9\-]{1,30})\.[a-z]{2,}',
    # https://stackoverflow.com/a/14051045/11039217
    'imei': r'[0-9]{15}(,[0-9]{15})*',
    # https://stackoverflow.com/a/36760050/11039217
    'ipv4_address': r'((25[0-5]|(2[0-4]|1[0-9]|[1-9]|)[0-9])(\.(?!$)|$)){4}',
    # https://stackoverflow.com/a/17871737/11039217
    'ipv6_address': r'(([0-9a-fA-F]{1,4}:){7,7}[0-9a-fA-F]{1,4}|([0-9a-fA-F]{1,4}:){1,7}:|([0-9a-fA-F]{1,4}:){1,6}:[0-9a-fA-F]{1,4}|([0-9a-fA-F]{1,4}:){1,5}(:[0-9a-fA-F]{1,4}){1,2}|([0-9a-fA-F]{1,4}:){1,4}(:[0-9a-fA-F]{1,4}){1,3}|([0-9a-fA-F]{1,4}:){1,3}(:[0-9a-fA-F]{1,4}){1,4}|([0-9a-fA-F]{1,4}:){1,2}(:[0-9a-fA-F]{1,4}){1,5}|[0-9a-fA-F]{1,4}:((:[0-9a-fA-F]{1,4}){1,6})|:((:[0-9a-fA-F]{1,4}){1,7}|:)|fe80:(:[0-9a-fA-F]{0,4}){0,4}%[0-9a-zA-Z]{1,}|::(ffff(:0{1,4}){0,1}:){0,1}((25[0-5]|(2[0-4]|1{0,1}[0-9]){0,1}[0-9])\.){3,3}(25[0-5]|(2[0-4]|1{0,1}[0-9]){0,1}[0-9])|([0-9a-fA-F]{1,4}:){1,4}:((25[0-5]|(2[0-4]|1{0,1}[0-9]){0,1}[0-9])\.){3,3}(25[0-5]|(2[0-4]|1{0,1}[0-9]){0,1}[0-9]))',
    # https://stackoverflow.com/a/4260512/11039217
    'mac_address': r'([0-9A-Fa-f]{2}[:-]){5}([0-9A-Fa-f]{2})',
    # https://stackoverflow.com/a/123666/11039217
    'us_phone_number': r'^(?:(?:\+?1\s*(?:[.-]\s*)?)?(?:\(\s*([2-9]1[02-9]|[2-9][02-8]1|[2-9][02-8][02-9])\s*\)|([2-9]1[02-9]|[2-9][02-8]1|[2-9][02-8][02-9]))\s*(?:[.-]\s*)?)?([2-9]1[02-9]|[2-9][02-9]1|[2-9][02-9]{2})\s*(?:[.-]\s*)?([0-9]{4})(?:\s*(?:#|x\.?|ext\.?|extension)\s*(\d+))?$',
    'words': r'_^' # Match nothing by default
}

def archive(path, regexes, password=None, verbose=False):
    filetype = mimetypes.guess_type(path, strict=False)
    if filetype[0] and filetype[0] in ['application/x-tar', 'application/zip']:
        tempdir = tempfile.TemporaryDirectory()
        try:
            with (tarfile.open(path) if filetype[0] == 'application/x-tar' else zipfile.ZipFile(path)) as archive:
               archive.extractall(path = tempdir.name) if filetype[0] == 'application/x-tar' else archive.extractall(path = tempdir.name, pwd = password.encode('utf-8'))
            directory(tempdir.name, regexes, recursive=True, verbose=verbose)
            return True
        except Exception as _:
            print(_)
            return True
        finally:
            tempdir.cleanup()
    return False

def directory(path, regexes, recursive=False, verbose=False):
    for child in os.listdir(path):
        child = path + os.path.sep + child
        if os.path.isfile(child):
            if not file(child, regexes, verbose):
                print('Skipping file with unsupported type: {}'.format(child))
        elif recursive and os.path.isdir(child):
            directory(path, regexes, recursive, verbose)

def file(path, regexes, verbose=False):
    binary = type(list(regexes.values())[0].pattern) == bytes
    with open_uncompressed(path, 'rb' if binary else 'r') as file:
        hits = list()
        data = file.read()
        for term, regex in regexes.items():
            hits = hits + [{'term': term, 'offset': hex(hit.span()[0]), 'match': str(hit[0])} for hit in re.finditer(regex, data)] if binary else \
                [{'term': term, 'line': hit[0], 'match': hit[1]} for term, regex in regexes.items() for hit in findall(data, regex, verbose)]
        if len(hits):
            generate_report(path, hits, binary)

def findall(string, regex, verbose=False, end='.*\n'):
    endings=[match.end() for match in re.finditer(end, string)]
    for match in regex.finditer(string):
        line = next((_ for _ in range(len(endings)) if endings[_] > match.start()))
        result = match.string[match.start():match.end()]
        if verbose:
            result = (string[(endings[line - 1] if line else 0):match.start()] + '[r]' + result + '[not r]' + string[match.end():endings[line]]).strip()
        yield (line + 1, result)

def generate_report(subject, hits, binary=False):
    reference = 'offset' if binary else 'line'
    table = Table(Column(header='Offset' if binary else 'Line', justify='right'), 'Search Term', Column(header='Match', no_wrap=True), title=subject)
    hits.sort(key=lambda item: item[reference])
    for hit in hits:
        table.add_row(str(hit[reference]), hit['term'], hit['match'])
    Console().print(table)

def open_uncompressed(path, *args, **kwargs):
    filetype =  mimetypes.guess_type(path)
    compressions = {'bzip2': bz2.open, 'gzip': gzip.open, 'xz': lzma.open}
    return (compressions[filetype[1]] if filetype[1] in compressions.keys() else open)(path, *args, **kwargs)

def main():
    import argparse
    import getpass

    parser = argparse.ArgumentParser(description='Scan for terms or identifiers in a file, directory, or archive.')
    parser.add_argument('-a', '--all', action='store_true', help='Search for all identifiers')
    parser.add_argument('-b', '--binary', action='store_true', help='Treat all files as binaries')
    parser.add_argument('-i', '--identifiers', type=str, help='Search for a subset of identifiers')
    parser.add_argument('-l', '--list', action='store_true', help='List the supported identifiers')
    parser.add_argument('-p', '--password', nargs='?', const=True, type=str, help='Archive password [default: prompt user]')
    parser.add_argument('-r', '--recursive', action='store_true', help='Scan a directory recursively')
    parser.add_argument('-v', '--verbose', action='store_true', help='Show the full lines that matches are found in')
    parser.add_argument('-w', '--wordlist', type=str, help='A file with words to search for, one per line')
    parser.add_argument('file', nargs='?', type=str, help='A file, directory, or archive to scan')
    args = parser.parse_args()
    regexes = {}
    if args.list:
        return print('Supported Identifiers:\n  {}'.format('\n  '.join(identifiers.keys())))
    if not args.all and not args.identifiers and not args.wordlist:
        return print('No wordlist or identifiers were specified for scanning.')
    if args.all:
        regexes = {term: re.compile(regex.encode('utf-8') if args.binary else regex, re.MULTILINE) for term, regex in identifiers.items()}
    elif args.identifiers:
        regexes = {term: re.compile(identifiers[term].encode('utf-8') if args.binary else identifiers[term], re.MULTILINE) for term in args.identifiers.split(',') if term in identifiers.keys()}
    if args.wordlist:
        with open(args.wordlist) as wordlist:
            regex = r'|'.join(wordlist.read().split())
            regexes['words'] = re.compile(regex.encode('utf-8') if args.binary else regex, re.MULTILINE | re.IGNORECASE)
    password = getpass.getpass(prompt='Password: ') if type(args.password) == bool else args.password if type(args.password) == str else ''
    
    if len(args.file) > 0:
        if os.path.isdir(args.file):
            directory(args.file, regexes, args.recursive, args.verbose)
        elif not archive(args.file, regexes, password, args.verbose):
            file(args.file, regexes, args.verbose)

if __name__ == '__main__':
    main()
