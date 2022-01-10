"""
Mint has become unbearable.  Let's create a Minimum Viable Alternative.

Central interface for adding new transactions.
"""
import admin
from cmd import Cmd
import argparse


def main():
    parser = argparse.ArgumentParser()

    parser.add_argument('filepath', nargs='?')
    parser.add_argument('account', nargs='?')

    args = parser.parse_args()

    if not args.filepath or not args.account:
        return

    admin.add_transactions_from_csv(
        args.filepath,
        args.account
    )


if __name__ == '__main__':
    main()

