import re
import copy
import shutil
from math import ceil
from datetime import datetime, timedelta

from . import const

def get_org_files(rcfile):
    """Get a list of org files from a 'vimrc' file."""
    vimrc = open(rcfile, 'r')
    data = vimrc.read()
    orgfiles = re.search(r'org_agenda_files\s=.*?\[.*?\]', data, re.DOTALL).group()
    orgfiles = orgfiles.split('[')[1].split(', ')
    orgfiles = [slugify(x) for x in orgfiles]

    return orgfiles

def get_todo_states(rcfile):
    """Get the 'TODO' states/keywords from a 'vimrc' file.

    Returns a dictionary for both the 'in progress' and 'completed' states.
    The values are regular expression pattern objects.

    For example, you may have the following in your '.vimrc':

        let g:org_todo_keywords =
            \ ['TODO(t)', 'DOING(s)', 'WAIT(w)', '|',
            \ 'DONE(d)', 'CANCELED(c)', 'DEFERRED(f)']

    In this case, the 'in progress' states are matched by 'TODO|DOING|WAIT',
    and similarly for the 'completed' states.
    """
    vimrc = open(rcfile, 'r')
    data = vimrc.read()
    todostates = re.search(r'org_todo_keywords\s=.*?\[.*?\]', data, re.DOTALL)

    if todostates is None:
        todostates = {
            'in_progress': re.compile('TODO'),
            'completed': re.compile('DONE')
        }
    else:
        todostates = todostates.group()
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
    """Calculate the (int) number of days left until a task's due date.

    Args:
        duedate (str): format should be '<%Y-%m-%d %a>' (including brackets)
    """
    dt = datetime.strptime(slugify(duedate), '%Y-%m-%d %a')
    timediff = dt - const.today
    return timediff.days

def day_names(str_):
    """Convert a date string to include full day name, padded.

    Args:
        str_ (str): the string should contain '<%Y-%m-%d %a>' (including
            brackets). It also works if ANSI sequences are present.

    Returns:
        A string with the date portion replaced by '%A %d %b', where '%A' is
        the full day name, and '%b' is the abbreviated month name. Spaces are
        added for padding the output.
    """
    match = const.regex['date'].search(str_).group()
    repl = datetime.strptime(match, '<%Y-%m-%d %a>').strftime('%A %d %b').split()
    repl = repl[0].ljust(10) + ' '.join(repl[1:])
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

def format_inline(str_, reset='normal'):
    """Format a string if there is any markup present."""
    if const.regex['url'].search(str_):
        text = slugify(str_.split('[[')[1].split('][')[1].split(']]')[0])
        str_ = const.regex['url'].sub(const.styles['url'] + text + const.styles[reset], str_)

    for key, val in const.inline.items():
        if val['pattern'].search(str_):
            matches = val['pattern'].findall(str_)
            repls = [val["cols"] + x.replace(val["delim"], "") + const.styles[reset]
                        for x in matches]
            for x, y in zip(matches, repls):
                str_ = str_.replace(x, y)

    return str_

# Main function applying styles to a line's dict object
#---------------------------------------
def colorize(dict_):
    """Apply ANSI sequences to specific dictionary entries.

    The input dictionary should be of the same format as those returned by
    'tree.OrgNode.parse()'.
    """
    styles = const.styles
    tagtype = 'tag'
    if re.search('urgent', dict_['tag'], re.IGNORECASE):
        tagtype = 'urgent'

    # Different styles for different todo states
    state = dict_['todostate'].strip().lower()
    dict_.update(todostate=styles[state] + dict_['todostate'].strip() + styles['normal'])

    # Scheduled vs Deadline
    dtype = dict_['date_two'].strip(': ').lower()
    if dtype != '':
        dict_.update(date_two=styles[dtype] + dict_['date_two'] + styles['normal'])
    else:
        dtype = 'normal'

    # Apply diff style depending on due date
    if dict_['days'] < 0:
        duedate = 'late'
    elif dict_['days'] == 0:
        duedate = 'today'
    else:
        duedate = 'later'
    dict_.update(tag=styles[tagtype] + dict_['tag'] + styles['normal'],
                 num_tasks=styles['checkbox'] + dict_['num_tasks'] + styles['normal'],
                 date_one=styles[duedate] + dict_['date_one'] + styles['normal'])

    if dict_['days'] > 0:
        dict_.update(category=styles['category'] + dict_['category'] + styles['normal'],
                     text=format_inline(dict_['text']) + styles['normal'])
    else:
        dict_.update(text=styles[dtype] + format_inline(dict_['text'], dtype) + styles['normal'],
                     category=styles[duedate] + dict_['category'])

    return dict_

# Function to update the line's dict for 'agenda' mode
#---------------------------------------
def update_agenda(list_, **kwargs):
    """Update entries if 'agenda' view is chosen."""
    styles = const.styles
    num_days = int(kwargs['num_days'])
    todolist = copy.deepcopy(list_)
    dates_agenda = []
    for i in range(num_days):
        dates_agenda.append((const.today + timedelta(i)).strftime('<%Y-%m-%d %a>'))

    repeat_tasks = []; deadline = []
    for d in todolist:
        if kwargs['colors']:
            if d['days'] > ceil(num_days / 2):
                deadline.append(styles['deadline_two'])
            else:
                deadline.append(styles['deadline'])
        else:
            deadline.append('')

    # Pad output if there are late tasks or larger 'num_days' is requested
    max_days = max([len(str(x['days'])) for x in todolist])
    for i, d in enumerate(todolist):
        if re.search('Deadline', d['date_two']):
            if 0 < d['days'] < num_days:
                day_str = str(d['days']).rjust(max_days+1)
                d_copy = dict(d)
                d_copy['date_one'] = const.regex['date'].sub(const.today_date, d['date_one'])
                d_copy['date_two'] = deadline[i] + ' In' + day_str + ' d.:' + styles['normal']
                repeat_tasks.append(d_copy)
            elif d['days'] < 0:
                day_str = str(d['days']).rjust(max_days)
                todolist[i].update(date_one=styles['late'] + const.today_date + '\n',
                                   date_two=deadline[i] + ' In ' + day_str + ' d.:' + styles['bright'])

    todolist = todolist + repeat_tasks

    # Add a blank entry for dates with no active tasks
    for d in dates_agenda:
        if not any(re.search(d, item) for item in [x['date_one'] for x in todolist]):
            blank_dict = {
                'date_one': styles['bright'] + d,
                'date_two': '', 'category': '', 'text': '', 'level': '',
                'num_tasks': '', 'tag': '', 'todostate': '', 'days': days_until_due(d)
            }
            todolist.append(blank_dict)

    todolist = sorted(todolist, key=lambda d: (const.regex['ansicolors'].sub('', d['date_one']), d['days']))

    # Change '<%Y-%m-%d %a>' to '%A %d %b' for all entries
    for i, d in enumerate(todolist):
        todolist[i]['date_one'] = day_names(d['date_one'])

    return todolist

#-------------------------------------------------------------------------------
# Main function concerned with parsing each task line/groups of lines
#-------------------------------------------------------------------------------
def get_parse_string(todostates):
    """Calculate the correct regex pattern for parsing an entire org line.

    Depends on the set of TODO "states"/keywords present in the files.

    Returns:
        A "re" pattern object (compiled) which can be matched into a dictionary
        with keys:
        - level     (the number of leading asterisks, e.g. "***")
        - todostate (one of "TODO", "DONE", etc.)
        - text      (the text of the task)
        - num_tasks (a box for tasks with multiple sub-tasks, e.g. "[2/5]")
        - date_one  (the date string, e.g. "Saturday  27 Feb";
                     can be blank if multiple tasks are due for a given date)
        - tag       (tags surrounded by ":", if present; e.g. ":work:urgent:")
        - date_two  (either the number of days until duedate, e.g. "In 5 d.:",
                     or "Deadline:" or "Scheduled:" with the date in format
                     "<%Y-%m-%d %a>")
    """
    # TODO The following gets *all* content between 2 consecutive headings/sets of asterisks
    # Should use this, in some way, to e.g. look for the date on line 2
    #all_content = re.findall(r'(?P<all>\*{1,9}.*?)(?:\n\*)', org.data, re.DOTALL)
    # TODO

    level_string = r'(?P<level>\*{1,9}|[^\S\n ]{1,9}-)'#\h{1,9}-)'
    todos = [x.pattern.split('|') for x in todostates.values()]
    todos = [item for sublist in todos for item in sublist]
    todos = [r'\s' + x + r'\s' for x in todos]
    todostate_string = r'(?P<todostate>(' + r'|'.join(todos) + r')|)'
    headerText_string = r'(?P<text>.*?)'
    numTasks_string = r'(?P<num_tasks>\s*\[\d+/\d+\]|)'
    date1 = r'(?P<date_one>' + const.date_str + '|)'
    tag_string = r'(?P<tag>[ \t]*:[\w:]*:)*'
    date2 = r'(?P<date_two>\n\s+[A-Z]+:\s' + const.date_str + r'(?:\n|$)|(?:\n|$))'
    line_string = level_string + todostate_string + headerText_string \
            + numTasks_string + date1 + tag_string + date2
    pattern_line = re.compile(line_string, re.MULTILINE)

    return pattern_line

#-------------------------------------------------------------------------------
# Print functions
#-------------------------------------------------------------------------------
def print_delim(n=30):
    """Print a line of blue '#' symbols."""
    print('\t\t' + const.styles['url'] + n*'#')

def print_header(**kwargs):
    """Print a colorful, informative header."""
    styles = const.styles
    if kwargs['colors']:
        print_delim(40)
        if kwargs['agenda']:
            if kwargs['num_days'] == 7:
                print('\t\t\t      {}WEEK AGENDA{}'.format(styles['checkbox'], styles['normal']))
            else:
                print('\t\t\t     {}{} DAY AGENDA{}'.format(styles['checkbox'], kwargs['num_days'], styles['normal']))
        elif kwargs['tags']:
            print('\t\t    {}Headlines with {}TAGS {}match: {}{}'.format(
                styles['checkbox'],
                styles['tag'],
                styles['checkbox'],
                styles['late'],
                kwargs['tags']))
        elif kwargs['categories']:
            print('\t\t {}Headlines with {}CATEGORY {}match: {}{}'.format(
                styles['checkbox'],
                styles['tag'],
                styles['checkbox'],
                styles['late'],
                kwargs['categories']))

        # All dates and tags
        else:
            if kwargs['states']:
                state = styles[kwargs['states'].lower()] + kwargs['states'].upper()
            else:
                state = styles['late'] + 'ALL'
            statelen = len(const.regex['ansicolors'].sub('', state))
            print('\t\t' + styles['checkbox'] + ' '*(5 - statelen) + 'Global list of ' \
                  + styles['todo'] + 'TODO' + styles['checkbox'] + ' items of type: ' + state)

        print_delim(40)

def print_all(list_, **kwargs):
    """Print the todo list lines, padding the columns."""
    #TODO can I use the terminal width in some way? Maybe if truncation is needed
    termwidth = shutil.get_terminal_size()[0]
    print_header(**kwargs)

    # Most of the rest of the function is an ugly hack to make sure everything
    # is aligned whether ANSI color sequences are present or not
    tag_lens = []; state_lens = []; text_lens = []; check_lens = []; cat_lens = []; date2_lens = []
    for _, d in enumerate(list_):
        state_lens.append(len(const.regex['ansicolors'].sub('', d['todostate'])))
        cat_lens.append(len(const.regex['ansicolors'].sub('', d['category'])))
        text_lens.append(len(const.regex['ansicolors'].sub('', d['text'])))
        check_lens.append(len(const.regex['ansicolors'].sub('', d['num_tasks'])))
        tag_lens.append(len(const.regex['ansicolors'].sub('', d['tag'])))
        date2_lens.append(len(const.regex['ansicolors'].sub('', d['date_two'])))

    longest_state = max(state_lens)
    if kwargs['agenda']:
        maxdatelen = 16     # Date string includes full day name
    else:
        maxdatelen = 14
    longest_cat = max(maxdatelen, max(cat_lens))
    longest_text = max(text_lens)
    longest_check = max(check_lens)
    longest_tag = max(tag_lens)
    longest_date = max(date2_lens)

    for i, d in enumerate(list_):
        d['date_one'] = re.sub('<|>', '', d['date_one'])
        d['category'] = d['category'] + ' '*(longest_cat + 1 - cat_lens[i])
        d['date_two'] = ' '*(longest_date + 1 - date2_lens[i]) + d['date_two']
        d['todostate'] = d['todostate'] + ' '*(longest_state + 2 - state_lens[i])
        d['num_tasks'] = d['num_tasks'] + ' '*(longest_text + 1 - text_lens[i]) \
            + ' '*(longest_check + 1 - check_lens[i])
        d['tag'] = d['tag'] + ' '*(longest_tag + 1 - tag_lens[i])
        #print(re.sub('<|>', '', d['date_one']) + '  ' + d['category'] \
        #      + d['date_two'] + '  ' + d['todostate'] + ' ' + d['text'] + d['num_tasks'] + d['tag'])
        print('{date_one} {category}{date_two} {todostate}{text}{num_tasks}{tag}'.format(**d))
