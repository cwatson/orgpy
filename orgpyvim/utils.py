import re
from datetime import datetime
from datetime import timedelta
from . import const
from colorama import init, Fore, Style
init(autoreset=True)

def get_org_files(rcfile):
    """Get a list of org files from a 'vimrc' file."""
    patt_files = re.compile(r'org_agenda_files\s=.*?\[.*?\]', re.DOTALL)
    vimrc = open(rcfile, 'r')
    data = vimrc.read()
    orgfiles = patt_files.search(data).group()
    orgfiles = orgfiles.split('[')[1].split(', ')
    orgfiles = [slugify(x) for _,x in enumerate(orgfiles)]

    return orgfiles

def get_todo_states(rcfile):
    """Get the 'TODO' states/keywords from a 'vimrc' file.

    Returns a dictionary for both the 'in progress' and 'completed' states.
    """
    patt_todostate = re.compile(r'org_todo_keywords\s=.*?\[.*?\]', re.DOTALL)
    vimrc = open(rcfile, 'r')
    data = vimrc.read()
    todostates = patt_todostate.search(data).group()

    todostates = [x.strip(', ') for x in slugify(todostates.split('[')[1]).split('|')]
    todostates = [re.compile(r'' + x.replace(', ', r'|') + r'') for x in todostates]
    todostates = {
        'in_progress': todostates[0],
        'completed': todostates[1]
    }

    return todostates

#-------------------------------------------------------------------------------
# Date-related functions
#-------------------------------------------------------------------------------
def compare_dates(duedate, duedate_dt, nondate):
    """Compare the given due date with today's date.

    Returns the input string with colors/styles applied based on the due date.
    """
    if duedate_dt < const.today:
        str_ = const.styles['late'] + duedate + nondate
    elif duedate_dt == const.today:
        str_ = const.styles['date'] + duedate + Fore.YELLOW + Style.BRIGHT + nondate
    elif const.today < duedate_dt <= const.today + timedelta(days=7):
        str_ = const.styles['date'] + duedate + Fore.GREEN + Style.BRIGHT + nondate
    else:
        str_ = const.styles['date'] + duedate + const.styles['normal'] + nondate

    return str_

#-------------------------------------------------------------------------------
# String formatting functions
#-------------------------------------------------------------------------------
def slugify(str_):
    """Remove single quotes, brackets, and newline characters from a string."""
    bad_chars = ["'", '[', ']', '\n', '<', '>' , '\\']
    for ch in bad_chars:
        str_ = str_.replace(ch, '')

    return str_

def format_str(str_):
    """Format a string if there is any markup present."""
    if const.urlpattern.search(str_):
        text = slugify(str_.split('[[')[1].split('][')[1].split(']]')[0])
        str_ = const.urlpattern.sub(const.styles['url'] + text + const.styles['normal'], str_)

    for key, val in const.patterns.iteritems():
        if val['pattern'].search(str_):
            matches = val['pattern'].findall(str_)
            repls = [val['cols'] + x.replace(val['delim'], "") + const.styles['normal']
                        for _,x in enumerate(matches)]
#            text = val['pattern'].search(str_).group().replace(val['delim'], "")
#            str_ = val['pattern'].sub(val['cols'] + text + const.styles['normal'], str_)
            for x,y in zip(matches, repls):
                str_ = str_.replace(x, y)

    return str_

def get_parse_string(todostates):
    """Calculate the correct regex pattern for parsing an entire org line.

    Depends on the set of TODO 'states'/keywords present in the files.
    """
    level_string = r'(?P<level>\*{1,9}|\s{1,9}-)'
    todos = [x.pattern.split('|') for x in todostates.values()]
    todos = [item for sublist in todos for item in sublist]
    todos = [r'\s' + x + r'\s' for x in todos]
    todostate_string = r'(?:(' + r'|'.join(todos) + r')|)'
    headerText_string = r'(?P<header>.*?)'
    numTasks_string = r'(?P<num_tasks>\s*\[\d+/\d+\]\s*|)'
    date_string = r'(?P<date>[\<\[]\d+-\d+-\d+\s[a-zA-Z]+[\>\]]|)'
    tag_string = r'(?P<tag>[ \t]*:[\w:]*:)*'
    line_string = level_string + todostate_string + headerText_string + \
            numTasks_string + date_string + tag_string + r'(\n)'
    pattern_line = re.compile(line_string)

    return pattern_line

#-------------------------------------------------------------------------------
# Print functions
#-------------------------------------------------------------------------------
def print_delim(n=30):
    """Print a line of blue '#' symbols."""
    print('\t\t' + const.styles['url'] + n*'#')

def print_color_key():
    print
    print_delim(50)
    print(const.styles['date'] + '\t\tCOLOR KEY' + '\n')
    print('Red background:    ' + const.styles['late'] + 'Overdue!')
    print('Yellow background: ' + Fore.YELLOW + Style.BRIGHT + 'Due today!')
    print('Green background:  ' + Fore.GREEN + Style.BRIGHT + 'Due in the next 7 days!')
    print('Black background:  ' + 'Due later')
    print_delim(50)
    print
