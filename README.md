# IMAPLoginTester

**IMAPLoginTester** is a simple Python script that reads a text file with lots of e-mails and passwords, and tries to check if those credentials are valid by trying to login to the respective IMAP servers.

**Usage:**
```
usage: imaplogintester.py [-h] -i INPUT [-o OUTPUT] [-s] [-t SLEEP_TIME] [-T TIMEOUT] [-P SOCKS5_PROXY] [-v]

optional arguments:
  -h, --help            show this help message and exit
  -i INPUT, --input INPUT
                        input file with e-mails and passwords
  -o OUTPUT, --output OUTPUT
                        save successes to output file
  -s, --show-successes  show successes only (no failures)
  -t SLEEP_TIME, --sleep-time SLEEP_TIME
                        set sleep time between tests (in seconds)
  -T TIMEOUT, --timeout TIMEOUT
                        set login requests timeout (in seconds)
  -P SOCKS5_PROXY, --socks5-proxy SOCKS5_PROXY
                        use a SOCKS5 proxy (eg: "localhost:9050")
  -v, --verbose         show verbose messages

```

**Preview:**

<a href="https://ibb.co/sF9BHDX"><img src="https://i.ibb.co/jLkpRxj/Screenshot-from-2021-05-14-10-17-53.png" alt="IMAPLoginTester screenshot" border="0"></a>
