from __future__ import absolute_import
import re, os, copy
from datetime import datetime
from . import const
from . import utils

__all__ = ['Orgfile', 'orgFromFile']

#===============================================================================
# Main class definition for entire org file
#===============================================================================
class Orgfile:
    """Class definition for an org file.

    Args:
        orgfile (str): full pathname of the org file
        todostates (dict): dictionary containing the 'in_progress' and
            'completed' TODO keywords
        **kwargs: dictionary containing the command-line arguments

    Attributes:
        active (list): list of lists of the active (incomplete) tasks
        basename (str): basename of the org file
        data (str): string containing all text in the org file
        orgfile (str)
        parsed (list): list of lists of each line, parsed
        pattern_line (:obj:`re`): regular expression object to parse each line
        todostates (dict)
        tags (list, optional): tags to filter by
        title (str, optional): title string, if present in the file
    """

    def __init__(self, orgfile, todostates, **kwargs):
        """Create a new Orgfile instance."""
        self.orgfile = orgfile
        self.basename = os.path.split(self.orgfile)[1]
        self.todostates = todostates
        self.tags = kwargs['tags']
        self.states = kwargs['states']
        self.pattern_line = utils.get_parse_string(self.todostates)

        f = open(orgfile, 'r')
        self.data = f.read()
        self.parse()

        # File-wide properties, if they exist
        if const.catpattern.search(self.data): self.apply_category()
        has_title = const.titlepattern.search(self.data)
        if has_title: self.title = has_title.group().split(':')[1].strip()

        self.get_active_todos()
        self.get_days_to_duedate()
        if kwargs['agenda']: self.subset_agenda()
        if kwargs['states']: self.subset_states()
        if kwargs['tags']: self.subset_tags()
        if kwargs['colors']: self.colorize()

    def __add__(self, other):
        """Concatenate the active TODOS of two 'Orgfile' objects."""
        return self.get_active_todos() + other.get_active_todos()

    def __len__(self):
        return len(self.active)

    #-------------------------------------------------------
    # Class methods
    #-------------------------------------------------------
    def parse(self):
        """Parse the given org file.

        Returns a list of lists, each with 6 elements:
            1. Level (i.e., # of asterisks, or spaces if it is a bare list)
            2. State (i.e., the "TODO" keyword for that line)
            3. Text (the actual text of the task/note)
            4. Number/percent of tasks completed (if the child list has checkboxes)
            5. Date string (active or inactive)
            6. Tag string (if tags are present)
        """
        matches = self.pattern_line.findall(self.data)
        ll = [list(x) for x in matches]
        self.parsed = ll

    def get_active_todos(self):
        """Return the lines with an active due date."""
        date_lines = []
        for _,x in enumerate(self.parsed):
            if x[4] != '': date_lines.append(x)

        in_prog = [x for x in date_lines if self.todostates['in_progress'].search(x[1])]
        self.active = in_prog

    def get_days_to_duedate(self):
        """Return a list of integers of the days left until the duedate."""
        days = []
        for i,x in enumerate(self.active):
            days.append(utils.days_until_due(x[4]))
        self.days = days

    def apply_category(self):
        """Add a 'tag' if there is a file-wide '#+CATEGORY' string."""
        category = const.catpattern.search(self.data).group().split(':')[1].strip()
        for i,x in enumerate(self.parsed):
            if x[5].strip() == '':
                self.parsed[i][5] = ':' + category + ':'
            else:
                self.parsed[i][5] = self.parsed[i][5] + category + ':'

    #-------------------------------------------------------
    # Methods to subset the tasks to be printed
    #-------------------------------------------------------
    def subset_agenda(self):
        """Subset the active todos if the 'agenda' option is specified."""
        todos = []; days = []
        for i,x in enumerate(self.days):
            if x < 7:
                todos.append(self.active[i])
                days.append(x)

        self.active = todos
        self.days = days

    def subset_tags(self):
        """Subset the active todos if the 'tags' option is specified."""
        todos = []; days = []
        for i,x in enumerate(self.active):
            if re.search(self.tags, x[5], re.IGNORECASE):
                todos.append(self.active[i])
                days.append(self.days[i])

        self.active = todos
        self.days = days

    def subset_states(self):
        """Subset the active todos if the 'states' option is specified."""
        todos = []; days = []
        for i,x in enumerate(self.active):
            if re.search(self.states, x[1], re.IGNORECASE):
                todos.append(self.active[i])
                days.append(self.days[i])

        self.active = todos
        self.days = days

    def colorize(self):
        """Colorize dates, tags, todo states, and inline text."""
        todos = copy.deepcopy(self.active)
        for i,x in enumerate(todos):
            if self.todostates['in_progress'].search(x[1]):
                if re.search('TODO', x[1]):
                    todos[i][1] = const.styles['todo'] + x[1].strip()
                else:
                    todos[i][1] = const.styles['started'] + x[1].strip()
                todos[i][1] += const.styles['normal']

            # Apply different styles depending on due date
            if self.days[i] > 0:
                todos[i][3] = const.styles['checkbox'] + x[3] + const.styles['normal']
                todos[i][4] = const.styles['date'] + x[4].strip() + const.styles['normal'] + '\n'
                todos[i][5] = const.styles['tag'] + x[5].strip().lstrip(':').title() + const.styles['normal']
                todos[i][2] = utils.format_inline(todos[i][2]) + const.styles['normal']
            else:
                if self.days[i] < 0:
                    todos[i][4] = const.styles['late'] + x[4].strip() + '\n'
                    todos[i][5] = const.styles['late'] + x[5].strip().lstrip(':').title()
                    todos[i][2] = const.styles['late'] + x[2]
                elif self.days[i] == 0:
                    todos[i][4] = const.styles['today'] + x[4].strip() + '\n'
                    todos[i][5] = const.styles['today'] + x[5].strip().lstrip(':').title()
                    todos[i][2] = const.styles['today'] + x[2]

        self.colored = todos


#-----------------------------------------------------------
# Function that will loop through all 'org' files listed in 'vimrc'
#-----------------------------------------------------------
def orgFromFile(**kwargs):
    """Get list of org files and TODO states from vimrc, read them, and print."""
    if kwargs['file']:
        orgfiles = kwargs['file'].split()
    else:
        orgfiles = utils.get_org_files(kwargs['rcfile'])

    todostates = utils.get_todo_states(kwargs['rcfile'])

    # Loop through the org files
    todolist = []
    for f in orgfiles:
        org = Orgfile(f, todostates, **kwargs)
        if kwargs['colors']:
            todolist += org.colored
        else:
            todolist += org.active

    # Add dates for the next week even if there are no tasks
    if kwargs['agenda']:
        for d in const.dates_agenda:
            if not any(re.search(d, item) for item in [x[4] for x in todolist]):
                todolist.append(['', '', '', '', const.styles['bright'] + d, '', '\n'])

    todolist = sorted(todolist, key=lambda x: const.ansicolors.sub('', x[4]))

    if kwargs['agenda']:
        for i,x in enumerate(todolist):
#            match = const.datepattern.search(x[4]).group()
#            repl = datetime.strptime(match, '<%Y-%m-%d %a>').strftime('%A %d %b %Y')
#            tmp = re.sub(match, repl, x[4])
#            todolist[i][4] = tmp
            todolist[i][4] = utils.day_names(x[4])

    # Remove repeating dates
    repeats = []
    for i,x in enumerate(todolist):
        if i > 0 and todolist[i][4] == todolist[i-1][4]:
            repeats.append(i)
    for i in repeats: todolist[i][4] = ''

    # Print
    if not todolist:
        print "No tasks!"; return
    else:
        utils.print_all(todolist, **kwargs)
