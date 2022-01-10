"""
Mint has become unbearable.  Let's create a Minimum Viable Alternative.

Central interface for adding new transactions.
"""
import admin
from cmd import Cmd
import argparse


class MyPrompt(Cmd):
    prompt = 'fun_money> '
    intro = "Welcome!"

    def __init__(self, args):
        super().__init__()
        self.args = args
        print(f'args are {args}')

    def do_exit(self, inp):
        print("Bye")
        return True

    def do_add(self, inp):
        if not self.args.filepath and self.args.account:
            print('not enough args to add')
            return

        print(f'Adding {self.args.filepath} to {self.args.account}')
        admin.add_transactions_from_csv(
            filepath=self.args.filepath,
            account_name=self.args.account
        )

    def default(self, line: str):
        print(f'would you like to add {self.args.filepath} to your {self.args.account} account?')


if __name__ == '__main__':
    parser = argparse.ArgumentParser()

    parser.add_argument('filepath', nargs='?')
    parser.add_argument('account', nargs='?')

    args = parser.parse_args()
    mp = MyPrompt(args)
    mp.cmdloop()

