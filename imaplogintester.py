#!/usr/bin/env python3
#
# IMAPLoginTester.py
# ------------------
# A simple Python script that reads a text file with the following content:
#
#   example1@gmail.com:myP4ssw0rd
#   example2@yahoo.com:@n0th3rp4$$
#   example3@hotmail.com:h3ll0th3r3!
#
# and tries to determine if the given credentials are valid by trying to
# connect and log into the respective IMAP servers.
#
# Coded by: Riccardo Mollo (riccardomollo84@gmail.com)
#

#### TODO:
#### - checks on filename at command line
#### - checks on 'domains.ini' file
#### - a lot of other stuff

import configparser
import imaplib
import pprint
import re
import signal
import sys
from termcolor import colored

def signal_handler(s, frame):
    if s == 2: # SIGINT
        print('You pressed Ctrl+C!')
        print('Goodbye!')
        sys.exit()

def green(str):
    return colored(str, 'green')

def red(str):
    return colored(str, 'red')

def yellow(str):
    return colored(str, 'yellow')

def warning(message):
    print(u'\u26A0', message)

def error(message):
    print(u'\u274C', message)

def email_is_valid(email):
    if (re.match('^[a-zA-Z0-9_+&*-]+(?:\\.[a-zA-Z0-9_+&*-]+)*@(?:[a-zA-Z0-9-]+\\.)+[a-zA-Z]{2,7}$', email) != None):
        return True

    return False

def result(email, password, result):
    e = yellow(email)
    p = yellow(password)
    r = green('SUCCEEDED') if result else red('FAILED')

    print("E-Mail: {} | Password: {} | Login: {}".format(e, p, r))

def test_login(account, domain, password, imap, port, ssl):
    try:
        if eval(ssl):
            connection = imaplib.IMAP4_SSL(imap, port = port, timeout = 5)
        else:
            connection = imaplib.IMAP4(imap, port = port, timeout = 5)

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
    config_file = 'domains.ini'
    config = configparser.ConfigParser()
    config.read(config_file)
    mail_re = '(^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$)'

    with open(sys.argv[1], 'r') as f:
        for row in f:
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
                    logged = test_login(account, domain, password, imap, port, ssl)
                    result(email, password, logged)
                else:
                    warning('Missing config section for domain: {}'.format(yellow(domain)))
            else:
                error('Invalid e-mail: {}'.format(yellow(email)))

if __name__ == '__main__':
    signal.signal(signal.SIGINT, signal_handler)

    if (len(sys.argv) != 2):
        print('Usage: ./imaplogintester.py <file.txt>')
    else:
        main(sys.argv[1:])
