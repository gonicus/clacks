#!/usr/bin/env python
import os
from time import sleep


def tail(path):
    # Start listening from the end of the given
    # path
    path.seek(0, 2)

    # Try to read until somthing new pops up
    while True:
         line = path.readline()

         if not line:
             sleep(0.1)
             continue

         yield line.strip()


def monitor(path):
    # Initialize dn, timestamp and change type.
    dn = None
    ts = None
    ct = None

    try:
        with open(path) as f:

            for line in tail(f):
                print line

                # Trigger on newline.

    except Exception as e:
        print "Error:", str(e)


def main():
    #TODO: args
    path = '/tmp/ldap-audit.socket'

    # Main loop
    while True:
        sleep(1)

        # Wait for file to pop up
        if not os.path.exists(path):
            continue

        # Wait for file to be file
        if not os.path.isfile(path):
            continue

        # Check if it is effectively readable
        try:
            with open(path) as f:
                pass
        except IOError as e:
            continue

        # Listen for changes
        monitor(path)


if __name__ == "__main__":
    main()
