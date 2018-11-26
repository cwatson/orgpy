import os, sys, argparse
import orgpyvim

def parse_cli(argv=None):
    """Parse an 'org' file to list TODO's, agendas, etc."""

    ex = """EXAMPLES:
    python -m orgpyvim --agenda --colors
    """
    parser = argparse.ArgumentParser(description=__doc__,
            formatter_class=argparse.RawDescriptionHelpFormatter,
            epilog=ex)
    parser.add_argument('--all',
                        action='store_true',
                        default=True,
                        help='Print all outstanding tasks with an active date.')
    parser.add_argument('-a', '--agenda',
                        action='store_true',
                        help='Show the weekly agenda)')
    parser.add_argument('-c', '--colors',
                        action='store_true',
                        default=False,
                        help='Print output with colors.')
    parser.add_argument('-t', '--tags',
                        action='store',
                        default=None,
                        help='Filter by tag(s).')
    parser.add_argument('-r', '--rcfile',
                        action='store',
                        default=os.path.expanduser('~/.vimrc'),
                        help='Vim config file containing vim-orgmode info.')
    parser.add_argument('-f', '--file',
                        action='store',
                        default=None,
                        help='A single org file to print information from.')

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
    orgpyvim.orgFromFile(**opts)

if __name__ == '__main__':
    run()
