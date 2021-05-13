#!/usr/bin/env python3
#
# IMAPLoginTester.py
# ------------------
# A simple Python script that reads a text file with the following content:
#
#   example1@gmail.com:myP4ssw0rd
#   example2@yahoo.com:@n0th3rp4$$
#   example3@hotmail.com:h3ll0th3r3!
#   [...]
#
# and tries to determine if the given credentials are valid by trying to
# connect to and log into the respective IMAP servers (options are defined in a
# config file).
#
# Coded by: Riccardo Mollo (riccardomollo84@gmail.com)
#

#### TODO:
#### - checks on 'domains.ini' file
#### - introduce multithreading

import argparse
import configparser
import imaplib
import os
import pprint
import re
import signal
import sys
import time
from termcolor import colored

def signal_handler(s, frame):
    if s == 2: # SIGINT
        print('You pressed Ctrl+C!')
        print('Goodbye!')
        sys.exit()

def green(text):
    return colored(text, 'green')

def red(text):
    return colored(text, 'red')

def yellow(text):
    return colored(text, 'yellow')

def warning(message):
    print(u'\u26A0', message)

def error(message):
    print(u'\u274C', message)

def email_is_valid(email):
    if (re.match('^[a-zA-Z0-9_+&*-]+(?:\\.[a-zA-Z0-9_+&*-]+)*@(?:[a-zA-Z0-9-]+\\.)+[a-zA-Z]{2,7}$', email) != None):
        return True
    else:
        return False

def check_for_file(file):
    if not os.path.isfile(file):
        print('Error! File "{}" not found or not readable.'.format(file))
        sys.exit(1)

def result(email, password, result, output_file):
    e = yellow(email)
    p = yellow(password)
    r = green('SUCCEEDED') if result else red('FAILED')

    print("E-Mail: {} | Password: {} | Login: {}".format(e, p, r))

    if result and output_file is not None:
        print(email + ':' + password, file = output_file)

def test_login(account, domain, password, imap, port, ssl, timeout):
    PYTHON_MIN_VER = sys.version_info[1]

    try:
        if eval(ssl):
            if (PYTHON_MIN_VER) >= 9:
                connection = imaplib.IMAP4_SSL(imap, port = port, timeout = timeout)
            else:
                connection = imaplib.IMAP4_SSL(imap, port = port)
        else:
            if (PYTHON_MIN_VER) >= 9:
                connection = imaplib.IMAP4(imap, port = port, timeout = timeout)
            else:
                connection = imaplib.IMAP4(imap, port = port)

        username = account + '@' + domain
        connection.login(username, password)

        if connection:
            connection.logout()

            return True
        else:
            return False
    except Exception as e:
        pass

def main(argv):
    parser = argparse.ArgumentParser(prog = 'imaplogintester.py')
    parser.add_argument('-i', '--input', help = 'input file with e-mails and passwords', required = True)
    parser.add_argument('-o', '--output', help = 'save successes to output file', required = False)
    parser.add_argument('-s', '--show-successes', help = 'show successes only (no failures)', required = False, action = 'store_true', default = None)
    parser.add_argument('-t', '--sleep-time', help = 'set sleep time between tests (in seconds)', required = False)
    parser.add_argument('-T', '--timeout', help = 'set login requests timeout (in seconds)', required = False)
    args = parser.parse_args()

    emails_file = args.input
    config_file = 'domains.ini'
    output_file = args.output
    sleep_time = args.sleep_time or 0
    timeout = args.timeout or 3 # default value is 3 seconds
    show_successes = args.show_successes

    check_for_file(emails_file)
    check_for_file(config_file)

    config = configparser.ConfigParser()
    config.read(config_file)

    of = None

    try:
        if (output_file is not None):
            of = open(output_file, 'a')
    except Exception as e:
        error('Can not write output to file: {}'.format(output_file))
        output_file = None
        of = None

    count_all = 0
    count_ok = 0

    with open(emails_file, 'r') as f:
        for row in f:
            try:
                row_tmp = row.split(':', 1)
                email = row_tmp[0].lower()
                password = row_tmp[1].strip()

                if email_is_valid(email):
                    email_tmp = email.split('@', 1)
                    account = email_tmp[0]
                    domain = email_tmp[1]

                    if domain in config:
                        imap = config[domain]['imap']
                        port = config[domain]['port']
                        ssl = config[domain]['ssl']
                        loggedin = test_login(account, domain, password, imap, port, ssl, timeout)

                        if (show_successes):
                            if (loggedin):
                                result(email, password, loggedin, of)
                        else:
                            result(email, password, loggedin, of)

                        count_all += + 1

                        if loggedin:
                            count_ok += 1

                        time.sleep(int(sleep_time))
                    else:
                        warning('Missing config section for domain: {}'.format(yellow(domain)))
                else:
                    error('Invalid e-mail: {}'.format(yellow(email)))
            except IndexError as indexerror:
                error('Wrong format for row: {}'.format(yellow(row.strip())))

    print('Working logins: ' + green(count_ok) + '/' + str(count_all))

    if (output_file is not None and of is not None):
        of.close()

if __name__ == '__main__':
    signal.signal(signal.SIGINT, signal_handler)
    main(sys.argv[1:])
