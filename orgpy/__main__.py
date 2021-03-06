import os
import sys
import argparse

import orgpy

def parse_cli(argv=None):
    """Parse an 'org' file to list TODO's, agendas, etc."""

    ex = """EXAMPLES:
    python3 -m orgpy --agenda --colors
    python3 -m orgpy -ct personal
    python3 -m orgpy -f ~/todo.org
    """
    parser = argparse.ArgumentParser(description=__doc__,
            formatter_class=argparse.RawDescriptionHelpFormatter,
            epilog=ex)
    parser.add_argument('-c', '--colors',
                        action='store_true', default=False,
                        help='Print output with colors')
    parser.add_argument('-a', '--agenda',
                        action='store_true',
                        help='Show the weekly agenda')
    parser.add_argument('-n', '--num_days',
                        action='store', type=int, default=7,
                        help='Choose the number of days for the agenda')
    parser.add_argument('-s', '--states',
                        action='store', default=None,
                        help='Filter by state(s) (i.e., TODO, STARTED, etc.)')
    parser.add_argument('-t', '--tags',
                        action='store', default=None,
                        help='Filter by tag(s)')
    parser.add_argument('-g', '--categories',
                        action='store', default=None,
                        help='Filter by category')
    parser.add_argument('-r', '--rcfile',
                        action='store', default=os.path.expanduser('~/.vimrc'),
                        help='Vim config file containing vim-orgmode info')
    parser.add_argument('-f', '--file',
                        action='store', default=None,
                        help='Choose a single org file to print information from')

    args = parser.parse_args(argv)
    return args

def run():
    """Run from the command line."""

    # Parse CLI options
    options = parse_cli()
    if not options:
        sys.exit(1)
    opts = vars(options)

    # Run
    orgpy.orgTreeFromFile(**opts)

if __name__ == '__main__':
    run()
