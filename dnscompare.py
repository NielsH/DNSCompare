#!/usr/bin/env python3

""""DNS Comparison Utility

Usage:
    dnscompare.py -s <secondary_nameserver> -f <file> [options]

Options:
    -h                          View this help text
    -q                          Only display errors
    -p <primary_nameserver>     IP of primary nameserver use [default: 208.67.222.222] (OpenDNS)
    -s <secondary_nameserver>   IP of nameserver to compare against
    -f <file>                   Newline separated list of domains with record types to query
                                example: example.org A,MX,CNAME

"""

import dns.resolver

from docopt import docopt
from ipaddress import ip_address
from colorama import Fore, init

init(autoreset=True)
resolver = dns.resolver.Resolver()
resolver.timeout = 2
resolver.lifetime = 2


def main(primary_ns, secondary_ns, input_file, quiet_mode):
    validate(primary_ns, secondary_ns, input_file)
    parse_data(primary_ns, secondary_ns, input_file, quiet_mode)


def parse_data(primary_ns, secondary_ns, input_file, quiet_mode):
    with open(input_file) as f:
        data = []
        # Parse all lines first to make sure none are invalid
        for line in valid_lines(f):
            data.append(get_line_data(line))

        for line in data:
            domain = line['domain']
            records = line['records']
            for record_type in records:
                primary_response = dns_query(primary_ns, domain, record_type)
                secondary_response = dns_query(secondary_ns, domain, record_type)
                result = ((compare_dns_response(domain, record_type,
                           primary_response, secondary_response)))
                if result.startswith(Fore.GREEN) and quiet_mode:
                    continue
                print(result)


def compare_dns_response(domain, record_type, primary_response, secondary_response):
    if None in primary_response or None in secondary_response:
        return('{0}Warning! At least 1 response was None, which means we were unable to get '
               'any type of response. This could have happened because of an error.\n'
               'Please manually verify the check for: {1} - {2} record.\n'
               'Primary NS: {3}\nSecondary NS: {4}\n'
               .format(Fore.YELLOW, domain, record_type,
                       '\n'.join(i for i in primary_response if i),
                       '\n'.join(i for i in secondary_response if i)))
    elif primary_response == secondary_response:
        return('{0}Success! {1} - {2} record.\nResponse:\n{3}\n'
               .format(Fore.GREEN, domain, record_type,
                       '\n'.join(i for i in primary_response if i)))
    else:
        return('{0}Error! Difference in DNS responses for {1} - {2} record.\n'
               'Primary NS: {3}\nSecondary NS: {4}\n'
               .format(Fore.RED, domain, record_type,
                       '\n'.join(i for i in primary_response if i),
                       '\n'.join(i for i in secondary_response if i)))


def dns_query(nameserver, domain, record_type):
    resolver.nameservers = [nameserver]
    try:
        return sorted([rdata.to_text() for rdata in resolver.query(domain, record_type)])
    except dns.resolver.NoAnswer:
        return ['\'\'']
    except dns.resolver.NoNameservers:
        return ['\'\'']
    except dns.resolver.NoMetaqueries:
        exit('{0}You used an invalid query type. Probably ANY, '
             'which is not supported. Exiting.\n'.format(Fore.RED))
    except dns.rdatatype.UnknownRdatatype:
        exit('{0}{1} contains invalid DNS record type: {2}\nExiting.'
             .format(Fore.RED, domain, record_type))
    except dns.exception.Timeout:
        print('{0}{1}Error! Timeout while querying the {2} record of {3} at nameserver {4}'
              .format(Fore.RED, record_type, domain, nameserver))
        return [None]


def get_line_data(line):
    data = {}
    try:
        l = line.split(' ')
        domain = l[0]
        records = l[1].split(',')
        data['domain'] = domain
        data['records'] = records
    except IndexError:
        exit('{0}Something went wrong while parsing the input_file.\n'
             'The line said: {1}\nExiting.\n'.format(Fore.RED, line))
    return data


def valid_lines(input_file):
    for line in input_file:
        l = line.strip()
        if l and not l.startswith('#'):
            yield l


def validate(primary_ns, secondary_ns, input_file):
    if not valid_ip(primary_ns):
        exit("Invalid IP for primary nameserver (-p flag)")
    elif not valid_ip(secondary_ns):
        exit("Invalid IP for secondary nameserver (-s flag)")
    elif not accessible_file(input_file):
        exit("Unable to access input file (-f flag)")
    return True


def valid_ip(ip):
    try:
        return ip_address(ip) and True
    except ValueError:
        return False


def accessible_file(input_file):
    try:
        f = open(input_file, 'r')
        f.close()
        return True
    except IOError:
        return False

if __name__ == '__main__':
    args = docopt(__doc__, version='DNS Comparison Utility v0.1')
    main(args['-p'], args['-s'], args['-f'], args['-q'])
