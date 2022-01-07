#!/usr/bin/env python3
# -*- coding: utf-8 -*-

'''File, directory, and archive scanning.'''

__all__ = [
    'archive', 'content', 'directory', 'file', 'main'
]

import os
import re
from rich.console import Console
from rich.table import Column, Table

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

def archive(file, regexes, password=''):
    # todo
    # tarfile, zipfile, gzip, bz2, mimetypes
    return False

def content(subject, data, regexes):
    hits = [{'term': term, 'line': hit[0], 'match': hit[1]} for term, regex in regexes.items() for hit in findall(regex, data)]
    if len(hits):
        generate_report(subject, hits)

def directory(path, regexes, recursive=False):
    for child in os.listdir(path):
        if os.path.isfile(child):
            file(child, regexes)
        elif recursive and os.path.isdir(child):
            directory(path, regexes, recursive)

def file(path, regexes):
    with open(path) as file:
        content(path, file.read(), regexes)
    return True

# modified from: https://stackoverflow.com/a/16674895/11039217
def findall(regex, string, flags=0, end='.*\n'):
    endings=[match.end() for match in re.finditer(end, string)]
    for match in regex.finditer(string):
        result = match.string[match.start():match.end()]
        yield (next((_ for _ in range(len(endings)) if endings[_] > match.start())), result)

def generate_report(subject, hits):
    table = Table(Column(header='List', justify='right'), 'Search Term', Column(header='Match', no_wrap=True), title=subject)
    hits.sort(key=lambda item: item['line'])
    for hit in hits:
        table.add_row(str(hit['line']), hit['term'], hit['match'])
    Console().print(table)

def main():
    import argparse
    import getpass

    parser = argparse.ArgumentParser(description='Scan for terms or identifiers in a file, directory, or archive.')
    parser.add_argument('-c', '--color', action='store_true', help='Highlight scan results')
    parser.add_argument('-i', '--identifiers', action='store_true', help='Search for all or a subset of identifiers')
    parser.add_argument('-l', '--list', action='store_true', help='List the supported identifiers')
    parser.add_argument('-p', '--password', nargs='?', const=True, type=str, help='Archive password [default: prompt user]')
    parser.add_argument('-r', '--recursive', action='store_true', help='Scan a directory recursively')
    parser.add_argument('-w', '--wordlist', type=str, help='A file with words to search for, one per line')
    parser.add_argument('file', nargs='?', type=str, help='A file, directory, or archive to scan')
    args = parser.parse_args()
    regexes = {term: re.compile(regex, re.MULTILINE) for term, regex in identifiers.items()}
    #if args.wordlist:
    #    regexes['words'] = re.compile(regex, re.MULTILINE | re.IGNORECASE)
    password = getpass.getpass(prompt='Password: ') if type(args.password) == bool else args.password if type(args.password) == str else ''
    if args.list:
        return print('Supported Identifiers:\n  {}'.format('\n  '.join(identifiers.keys())))
    if len(args.file) > 0:
        if os.path.isdir(args.file):
            directory(args.file, regexes, args.recursive)
        elif not archive(args.file, regexes, password) and not file(args.file, regexes):
            print('File type not supported.')

if __name__ == '__main__':
    main()