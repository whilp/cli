#!/usr/bin/env python
import cli.app

@cli.app.CommandLineApp
def ls(app):
    pass

ls.add_param("-l", "--long", help="list in long format", default=False, action="store_true")

if __name__ == "__main__":
    ls.run()
