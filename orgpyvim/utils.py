import re
from datetime import datetime
from . import const

def get_org_files(rcfile):
    """Get a list of org files from a 'vimrc' file."""
    vimrc = open(rcfile, 'r')
    data = vimrc.read()
    orgfiles = const.regex['orgfile'].search(data).group()
    orgfiles = orgfiles.split('[')[1].split(', ')
    orgfiles = [slugify(x) for x in orgfiles]

    return orgfiles

def get_todo_states(rcfile):
    """Get the 'TODO' states/keywords from a 'vimrc' file.

    Returns a dictionary for both the 'in progress' and 'completed' states.
    """
    vimrc = open(rcfile, 'r')
    data = vimrc.read()
    todostates = const.regex['todostates'].search(data).group()

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
    match = const.regex['date'].search(str_).group()
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
    for ch in bad_chars: str_ = str_.replace(ch, '')

    return str_

def format_inline(str_, reset='normal'):
    """Format a string if there is any markup present."""
    if const.regex['url'].search(str_):
        text = slugify(str_.split('[[')[1].split('][')[1].split(']]')[0])
        str_ = const.regex['url'].sub(const.styles['url'] + text + const.styles[reset], str_)

    for key, val in const.inline.iteritems():
        if val['pattern'].search(str_):
            matches = val['pattern'].findall(str_)
            repls = [val['cols'] + x.replace(val['delim'], '') + const.styles[reset]
                        for x in matches]
            for x,y in zip(matches, repls):
                str_ = str_.replace(x, y)

    return str_

#-------------------------------------------------------------------------------
# Main function concerned with parsing each task line/groups of lines
#-------------------------------------------------------------------------------
def get_parse_string(todostates):
    """Calculate the correct regex pattern for parsing an entire org line.

    Depends on the set of TODO 'states'/keywords present in the files.
    """
    # TODO The following gets *all* content between 2 consecutive headings/sets of asterisks
    # Should use this, in some way, to e.g. look for the date on line 2
    #all_content = re.findall(r'(?P<all>\*{1,9}.*?)(?:\n\*)', org.data, re.DOTALL)
    # TODO

    level_string = r'(?P<level>\*{1,9}|\h{1,9}-)'
    todos = [x.pattern.split('|') for x in todostates.values()]
    todos = [item for sublist in todos for item in sublist]
    todos = [r'\s' + x + r'\s' for x in todos]
    todostate_string = r'(?P<todostate>(' + r'|'.join(todos) + r')|)'
    headerText_string = r'(?P<text>.*?)'
    numTasks_string = r'(?P<num_tasks>\s*\[\d+/\d+\]\s*|)'
#    date1 = r'(?P<date_one>[\<\[]\d{4}-\d{2}-\d{2}\s[a-zA-Z]{3}[\>\]]|)'
    date1 = r'(?P<date_one>' + const.date_str + '|)'
    tag_string = r'(?P<tag>[ \t]*:[\w:]*:)*'
    date2 = r'(?P<date_two>\n\s+[A-Z]+:\s' + const.date_str + r'(?:\n|$)|(?:\n|$))'
    line_string = level_string + todostate_string + headerText_string + \
            numTasks_string + date1 + tag_string + date2
    pattern_line = re.compile(line_string, re.MULTILINE)

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
                state = const.styles[kwargs['states'].lower()] + kwargs['states'].upper()
            else:
                state = const.styles['late'] + 'ALL'
            print '\t\t' + const.styles['checkbox'] + 'Global list of ' + \
                const.styles['todo'] + 'TODO' + const.styles['checkbox'] + ' items of type: ' + state

        print_delim(40)

def print_all(list_, **kwargs):
    """Print the todo list lines, padding the columns."""
    tag_lens = []; state_lens = []; text_lens = []; check_lens = []
    for i,d in enumerate(list_):
        state_lens.append(len(const.regex['ansicolors'].sub('', d['todostate'])))
        tag_lens.append(len(const.regex['ansicolors'].sub('', d['category'])))
        text_lens.append(len(const.regex['ansicolors'].sub('', d['text'])))
        check_lens.append(len(const.regex['ansicolors'].sub('', d['num_tasks'])))

    longest_state = max(state_lens)
    if kwargs['agenda']:
        maxdatelen = 22     # Date string includes full day name
    else:
        maxdatelen = 18
    longest_tag = max(maxdatelen, max(tag_lens))
    longest_text = max(text_lens)
    longest_check = max(check_lens)
    print_header(**kwargs)
    for i,d in enumerate(list_):
        d['todostate'] = d['todostate'] + ' '*(longest_state + 2 - state_lens[i])
        d['category'] = d['category'] + ' '*(longest_tag + 1 - tag_lens[i])
        d['num_tasks'] = d['num_tasks'] + ' '*(longest_text + 1 - text_lens[i]) + \
            ' '*(longest_check + 1 - check_lens[i])
        print re.sub('<|>', '', d['date_one']) + '  ' + d['category'] + \
            d['date_two'] + '  ' + d['todostate'] + ' ' + d['text'] + d['num_tasks'] + d['tag']
