#!/usr/bin/env python3
# -*- coding: utf-8 -*-

'''BloodHound database class.'''

__all__ = [
    'BloodHoundDatabase', 'get_names', 'main'
]

import neo4j
import sys

class BloodHoundDatabase(neo4j.GraphDatabase):
    def __init__(self, uri, username, password):
        super().__init__()
        self.connected = False
        self.reconnect(uri, username, password)
        
    __list = lambda self, attribute, dry_run=False: self.query('MATCH (node {%s: true}) RETURN node.name' % (attribute), dry_run)
    __set = lambda self, name, attribute, value, dry_run: self.query('MATCH (node {name: \'%s\'}) SET node.%s = %s, node.manuallyset = true RETURN COUNT(*) AS count' % (name, attribute, value), dry_run)
    list_high_value = lambda self, dry_run=False: self.__list('highvalue', dry_run)
    list_owned = lambda self, dry_run=False: self.__list('owned', dry_run)
    set_high_value = lambda self, name, status=True, dry_run=False: self.__set(name, 'highvalue', 'true' if status else 'false', dry_run)
    set_owned = lambda self, name, status=True, dry_run=False: self.__set(name, 'owned', 'true' if status else 'false', dry_run)

    def query(self, cypher, dry_run=False):
        if dry_run:
            return 'Query: ' + cypher
        else:
            with self.driverInstance.session() as session:
                try:
                    return session.run(cypher).data()
                except neo4j.exceptions.Neo4jError as error:
                    return error.message
                except neo4j.exceptions.ServiceUnavailable:
                    return 'Could not connect to database.'
                except ValueError as error:
                    return 'You must provide a query to run.'
                
    def reconnect(self, uri, username='', password=''):
        self.driverInstance = self.driver(uri, auth = neo4j.Auth(scheme='basic', principal=username, credentials=password))
        self.connected = True

def get_names(names):
    '''Generate a list or names from a comma separated list or stdin if no list is given.

    :param names: A list of names
    :type names: list
    :return: A yielded name
    :rtype: str
    '''
    if len(names) == 0:
        for line in sys.stdin:
            yield line.strip()
    else:
        for name in names.split(','):
            yield name

def main():
    import argparse
    import getpass
    import readline # implicitly used by rich.Console.input
    import rich
    import rich.console

    parser = argparse.ArgumentParser(description='Query or modify a BloodHound database.')
    parser.add_argument('-d', '--dry-run', action='store_true', help='Show changes required to apply markings')
    parser.add_argument('-p', '--password', nargs='?', const=True, type=str, help='Connection password [default: prompt user]')
    parser.add_argument('-u', '--uri', default='bolt://localhost:7687', type=str, help='Specify alternate port [default: bolt://localhost:7687]')
    parser.add_argument('--username', default='neo4j', type=str, help='Connection username [default: neo4j]')
    group = parser.add_mutually_exclusive_group()
    group.add_argument('-l', '--list', action='store_true', help='List all owned and high value nodes')
    group.add_argument('-q', '--query', type=str, help='Run cypher query')
    group.add_argument('-r', '--reset', nargs='?', const=True, type=str, help='Reset item(s) as owned or high value')
    group.add_argument('-s', '--set', nargs='?', const=True, type=str, help='Set item(s) as owned or high value')
    group = parser.add_argument_group(title='Node Type')
    group.add_argument('-o', '--owned', action='store_true', help='List or set nodes as owned')
    group.add_argument('-v', '--high-value', action='store_true', help='List or set nodes as high value')
    args = parser.parse_args()
    password = getpass.getpass(prompt='Password: ') if not args.password or type(args.password) == bool else args.password
    database = BloodHoundDatabase(args.uri, username=args.username, password=password)

    print = lambda output: rich.console.Console().print(output)
    if database.connected:
        if args.list:
            if args.high_value or not args.owned:
                print(database.list_high_value(args.dry_run))
            if args.owned or not args.high_value:
                print(database.list_owned(args.dry_run))
        elif args.query:
            print(database.query(args.query, args.dry_run))
        elif any(_ in [type(args.set), type(args.reset)] for _ in (bool, str)):
            status = True if args.set else False
            argument = args.set if args.set else args.reset
            for name in get_names(argument if type(argument) == str else ''):
                if args.high_value or not args.owned:
                    print(database.set_high_value(name, status, args.dry_run))
                if args.owned or not args.high_value:
                    print(database.set_owned(name, status, args.dry_run))
        else:
            console = rich.console.Console()
            queryNumber = 0
            while True:
                output = database.query(console.input('In [{}]: '.format(queryNumber)))
                successful = type(output) == list
                console.print('Out[{}]:{}'.format(queryNumber, '' if successful else ('\n{}' if '\n' in output else ' {}').format(output)))
                if successful:
                    console.print(output)
                queryNumber += 1
    else:
        print('Could not connect to database at {}'.format(args.uri))

if __name__ == '__main__':
    try:
        main()
    except BrokenPipeError as _:
        sys.exit(_.errno)
    except KeyboardInterrupt as _:
        print()