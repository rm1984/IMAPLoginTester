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
import re
import signal
import sys
import time
import socks
import validators
from termcolor import colored


def signal_handler(sign, frame):
    print(frame)
    if sign == 2:  # SIGINT
        print("You pressed Ctrl+C!")
        print("Goodbye!")
        sys.exit()


def green(text):
    return colored(text, "green")


def red(text):
    return colored(text, "red")


def yellow(text):
    return colored(text, "yellow")


def warning(message):
    print("\u26A0", message)


def error(message):
    print("\u274C", message)


def email_is_valid(email):
    return (
        re.match(
            "^[a-zA-Z0-9_+&*-]+(?:\\.[a-zA-Z0-9_+&*-]+)*@(?:[a-zA-Z0-9-]+\\.)+[a-zA-Z]{2,7}$",
            email,
        )
        is not None
    )


def check_for_file(file):
    if not os.path.isfile(file):
        print('Error! File "{}" not found or not readable.'.format(file))

        sys.exit(1)


def result(email, password, success, output_file):
    eml = yellow(email)
    pwd = yellow(password)
    res = green("SUCCEEDED") if success else red("FAILED")

    print("E-Mail: {} | Password: {} | Login: {}".format(eml, pwd, res))

    if success and output_file is not None:
        print(email + ":" + password, file=output_file)
        output_file.flush()


def split_host_port(hostport):
    if hostport.find(":") == -1:
        error('Error! SOCKS5_PROXY value must be in the "hostname:port" format.')

        sys.exit(1)

    hostport = hostport.rsplit(":", 1)

    host = hostport[0]
    port = int(hostport[1])

    if host != "localhost" and not (validators.domain(host) or validators.ipv4(host)):
        error('SOCKS5 proxy host "{}" is not valid.'.format(host))

        sys.exit(1)
    else:
        return (host, port)


def test_login(
    account,
    domain,
    password,
    imap,
    port,
    ssl,
    timeout,
    socks5_proxy,
    show_successes,
    verbose,
):
    ret = False

    if not (validators.domain(imap) or validators.ipv4(imap)):
        error('IMAP server "{}" is not valid.'.format(imap))

        return ret

    try:
        if socks5_proxy:
            (proxy_host, proxy_port) = split_host_port(socks5_proxy)

            socks.setdefaultproxy(socks.PROXY_TYPE_SOCKS5, proxy_host, proxy_port)
            socks.socket.setdefaulttimeout(30)
            socks.wrapmodule(imaplib)

        python_min_ver = sys.version_info[1]

        if ssl == "True":
            if (python_min_ver) >= 9:
                connection = imaplib.IMAP4_SSL(imap, port=port, timeout=timeout)
            else:
                connection = imaplib.IMAP4_SSL(imap, port=port)
        elif ssl == "False":
            if (python_min_ver) >= 9:
                connection = imaplib.IMAP4(imap, port=port, timeout=timeout)
            else:
                connection = imaplib.IMAP4(imap, port=port)
        else:
            if not show_successes:
                error(
                    'Wrong value for "ssl" parameter in "{}"" domain: {}'.format(
                        domain, red(ssl)
                    )
                )
            else:
                pass

        username = account + "@" + domain
        connection.login(username, password)

        if connection:
            connection.logout()
            ret = True

        return ret
    except Exception as ex:
        if verbose and not show_successes:
            error(ex)

        return ret


def main():
    parser = argparse.ArgumentParser(prog="imaplogintester.py")
    parser.add_argument(
        "-i", "--input", help="input file with e-mails and passwords", required=True
    )
    parser.add_argument(
        "-o", "--output", help="save successes to output file", required=False
    )
    parser.add_argument(
        "-s",
        "--show-successes",
        help="show successes only (no failures and no warnings/errors)",
        required=False,
        action="store_true",
        default=None,
    )
    parser.add_argument(
        "-t",
        "--sleep-time",
        help="set sleep time between tests (in seconds)",
        required=False,
    )
    parser.add_argument(
        "-T",
        "--timeout",
        help="set login requests timeout (in seconds)",
        required=False,
    )
    parser.add_argument(
        "-P",
        "--socks5-proxy",
        help='use a SOCKS5 proxy (eg: "localhost:9050")',
        required=False,
    )
    parser.add_argument(
        "-v",
        "--verbose",
        help="show verbose messages",
        required=False,
        action="store_true",
        default=None,
    )
    args = parser.parse_args()

    config_file = (
        os.path.abspath(os.path.dirname(sys.argv[0])) + os.path.sep + "domains.ini"
    )
    emails_file = args.input
    output_file = args.output
    show_successes = args.show_successes
    sleep_time = args.sleep_time or 0  # default value is 0 seconds
    timeout = args.timeout or 3  # default value is 3 seconds
    socks5_proxy = args.socks5_proxy
    verbose = args.verbose

    print()
    print("\u2709", "IMAPLoginTester", "\u2709")
    print()

    check_for_file(emails_file)
    check_for_file(config_file)

    config = configparser.ConfigParser()
    config.read(config_file)

    output_file_handle = None

    try:
        if output_file is not None:
            output_file_handle = open(output_file, "a", encoding="utf-8")
    except Exception:
        error("Can not write output to file: {}".format(output_file))
        output_file = None
        output_file_handle = None

    count_all = 0
    count_ok = 0

    if verbose:
        print("E-Mails file:      {}".format(emails_file))
        print("Logins to test:    {}".format(len(open(emails_file).readlines())))
        print("Output file:       {}".format(output_file))
        print("Sleep time:        {} seconds".format(sleep_time))
        print("Login timeout:     {} seconds".format(timeout))
        print("SOCKS5 proxy:      {}".format(socks5_proxy))
        print()

    with open(emails_file, "r", encoding="utf-8") as emails_file_handle:
        for row in emails_file_handle:
            try:
                row_tmp = row.split(":", 1)
                email = row_tmp[0].lower()
                password = row_tmp[1].strip()

                if email_is_valid(email):
                    email_tmp = email.split("@", 1)
                    account = email_tmp[0]
                    domain = email_tmp[1]

                    if domain in config:
                        imap = config[domain]["imap"]
                        port = config[domain]["port"]
                        ssl = config[domain]["ssl"]

                        loggedin = test_login(
                            account,
                            domain,
                            password,
                            imap,
                            port,
                            ssl,
                            int(timeout),
                            socks5_proxy,
                            show_successes,
                            verbose,
                        )

                        if show_successes:
                            if loggedin:
                                result(email, password, loggedin, output_file_handle)
                        else:
                            result(email, password, loggedin, output_file_handle)

                        count_all += +1

                        if loggedin:
                            count_ok += 1

                        time.sleep(int(sleep_time))
                    else:
                        if not show_successes:
                            warning(
                                "Missing config section for domain: {}".format(
                                    yellow(domain)
                                )
                            )
                else:
                    if not show_successes:
                        error("Invalid e-mail: {}".format(yellow(email)))
            except IndexError:
                if not show_successes:
                    error("Wrong format for row: {}".format(yellow(row.strip())))

    if count_ok == 0:
        print("Working logins:    " + red(count_ok) + "/" + str(count_all))
    else:
        print()
        print("Working logins:    " + green(count_ok) + "/" + str(count_all))

    if output_file is not None and output_file_handle is not None:
        output_file_handle.close()


if __name__ == "__main__":
    signal.signal(signal.SIGINT, signal_handler)
    main()
