import re
from datetime import datetime
from . import const

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

    todostates = re.sub(r'\([a-z]\)', '', todostates)
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
def days_until_due(duedate):
    """Calculate the number of days left until a task's due date."""

    dt = datetime.strptime(slugify(duedate), '%Y-%m-%d %a')
    timediff = dt - const.today
    return timediff.days

def day_names(str_):
    """Convert a date string (w/ ANSI colors) to include full day name, padded."""
    match = const.datepattern.search(str_).group()
    repl = datetime.strptime(match, '<%Y-%m-%d %a>').strftime('%A %d %b %Y')
    repl = repl.split()[0] + ' '*(10 - len(repl.split()[0])) + ' '.join(repl.split()[1:4])
    tmp = re.sub(match, repl, str_)
    return tmp

#-------------------------------------------------------------------------------
# String formatting functions
#-------------------------------------------------------------------------------
def slugify(str_):
    """Remove single quotes, brackets, and newline characters from a string."""
    bad_chars = ["'", '[', ']', '\n', '<', '>' , '\\']
    for ch in bad_chars:
        str_ = str_.replace(ch, '')

    return str_

def format_inline(str_):
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
    todostate_string = r'(?P<todostate>(' + r'|'.join(todos) + r')|)'
#TODO below line is older; above works w/ "re.finditer"
#    todostate_string = r'(?:(' + r'|'.join(todos) + r')|)'
    headerText_string = r'(?P<header>.*?)'
    numTasks_string = r'(?P<num_tasks>\s*\[\d+/\d+\]\s*|)'
    date_string = r'(?P<date>[\<\[]\d+-\d+-\d+\s[a-zA-Z]+[\>\]]|)'
    tag_string = r'(?P<tag>[ \t]*:[\w:]*:)*'
    endline = r'(?P<endline>\n|$)'
    line_string = level_string + todostate_string + headerText_string + \
            numTasks_string + date_string + tag_string + endline#r'(?P<endline>\n)'
    pattern_line = re.compile(line_string)

    return pattern_line

#-------------------------------------------------------------------------------
# Print functions
#-------------------------------------------------------------------------------
def print_delim(n=30):
    """Print a line of blue '#' symbols."""
    print('\t\t' + const.styles['url'] + n*'#')

def print_header(**kwargs):
    if kwargs['colors']:
        print_delim(40)
        if kwargs['agenda']:
            print('\t\t\t    ' + const.styles['checkbox'] + 'WEEK AGENDA' + \
                    const.styles['normal'])
        elif kwargs['tags']:
            print('\t\t    ' + const.styles['checkbox'] + 'Headlines with ' + \
                    const.styles['tag'] + 'TAGS ' + const.styles['checkbox'] + 'match: ' + \
                    const.styles['late'] + '%s' % kwargs['tags'])
        elif kwargs['categories']:
            print('\t\t ' + const.styles['checkbox'] + 'Headlines with ' + \
                    const.styles['tag'] + 'CATEGORY ' + const.styles['checkbox'] + 'match: ' + \
                    const.styles['late'] + '%s' % kwargs['categories'])

        # All dates and tags
        else:
            if kwargs['states']:
                last = const.styles[kwargs['states'].lower()] + kwargs['states'].upper()
            else:
                last = const.styles['late'] + 'ALL'
            print '\t\t' + const.styles['checkbox'] + 'Global list of TODO items of type: ' + last

        print_delim(40)

def print_all(todolist, **kwargs):
    """Print the todo list lines, padding the columns."""
    tag_lens = []; state_lens = []
    for i,x in enumerate(todolist):
        state_lens.append(len(const.ansicolors.sub('', x[1])))
        tag_lens.append(len(const.ansicolors.sub('', x[5])))

    longest_state = max(state_lens)
    if kwargs['agenda']:
        maxdatelen = 22     # Date string includes full day name
    else:
        maxdatelen = 18
    longest_tag = max(maxdatelen, max(tag_lens))
    print_header(**kwargs)
    for i,x in enumerate(todolist):
        x[1] = x[1] + ' '*(longest_state + 2 - state_lens[i])
        x[5] = x[5] + ' '*(longest_tag + 1 - tag_lens[i])
        print re.sub('<|>', '', x[4]) + '  ' + x[5] + ' '.join(x[1:4]) + x[6],
