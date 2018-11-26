from __future__ import absolute_import
import re, os
from datetime import datetime
from datetime import timedelta
from . import const
from . import utils

__all__ = ['Orgfile', 'orgFromFile']

#===============================================================================
# Main class definition for entire org file
#===============================================================================
class Orgfile:
    """Class definition for an org file."""

    def __init__(self, orgfile, todostates, **kwargs):
        """Create a new Orgfile instance."""
        self.orgfile = orgfile
        self.basename = os.path.split(self.orgfile)[1]
        self.todostates = todostates
        self.tags = kwargs['tags']
        self.pattern_line = utils.get_parse_string(self.todostates)

        f = open(orgfile, 'r')
        self.data = f.read()
        self.parsed = self.parse()

        # File-wide properties, if they exist
        if const.catpattern.search(self.data):
            self.apply_category()
        has_title = const.titlepattern.search(self.data)
        if has_title:
            self.title = has_title.group().split(':')[1].strip()

        self.active = self.get_active_todos()

    def __add__(self, other):
        """Concatenate the active TODOS of two 'Orgfile' objects."""
        return self.get_active_todos() + other.get_active_todos()

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
        return ll

    def get_active_todos(self):
        """Return the lines with an active due date."""
        date_lines = []
        for _,x in enumerate(self.parsed):
            if x[4] != '':
                date_lines.append(x)

        in_prog = [x for x in date_lines if self.todostates['in_progress'].search(x[1])]
        return in_prog

    def apply_category(self):
        """Add a 'tag' if there is a file-wide '#+CATEGORY' string."""
        category = const.catpattern.search(self.data).group().split(':')[1].strip()
        for i,x in enumerate(self.parsed):
            if x[5].strip() == '':
                self.parsed[i][5] = ':' + category + ':'
            else:
                self.parsed[i][5] = self.parsed[i][5] + category + ':'


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
#    dict_ = {}; alldates = []; alltodos = []
    todolist = []
    for f in orgfiles:
        org = Orgfile(f, todostates, **kwargs)
        todolist += org.get_active_todos()
#        dl = listDates(f, todostates)
#        if len(dl) > 0:
#            dict_[org.basename] = {'dates': dl[0], 'lines': dl[1]}
#            base = os.path.split(f)[1]
#            dict_[base] = {'dates': dl[0], 'lines': dl[1]}

#    for k,v in dict_.iteritems():
#        alldates += v['dates']
#        alltodos += v['lines']

    todolist = sorted(todolist, key=lambda x: x[4])

    # Print all tasks
    #-------------------------------------------------------
#    for k,v in dict_.iteritems():
#        if len(v) > 0:
#            print(const.styles['file'] + os.path.splitext(k)[0].upper())
#            for x in v['lines']: print(x)
#            print

    # Agenda
    #-------------------------------------------------------
    if kwargs['agenda']:
        if kwargs['colors']:
            utils.print_delim()
            print('\t\t\t' + const.styles['todo'] + 'WEEKLY AGENDA' + const.styles['normal'])
            utils.print_delim()
        else:
            print('\t\t\tWEEKLY AGENDA')

        agenda = []
        for _,x in enumerate(todolist):
            if x[4].strip() != '':
                dt = datetime.strptime(utils.slugify(x[4]), '%Y-%m-%d %a')
                if dt < const.today + timedelta(days=7):
                    agenda.append(x)

        todolist = agenda
        #dl_sorted = zip(*sorted(zip(alldates, alltodos)))

    # Tags
    #-------------------------------------------------------
    if kwargs['tags']:
        taglist = []
        for _,x in enumerate(todolist):
            if re.search(kwargs['tags'], x[5], re.IGNORECASE):
                taglist.append(x)

        todolist = taglist

    # Remove repeating dates; record tag lengths
    #-------------------------------------------------------
    late = []; repeats = []; taglengths = []
    for i,x in enumerate(todolist):
        if x[4].strip() != '':
            if i > 0 and todolist[i][4] == todolist[i-1][4]:
                repeats.append(i)
        if datetime.strptime(utils.slugify(x[4]), '%Y-%m-%d %a') < const.today:
            late.append(i)
        taglengths.append(len(x[5].strip().lstrip(':')))

    # Colors
    #-------------------------------------------------------
    if kwargs['colors']:
        #utils.print_color_key()
        for i,x in enumerate(todolist):
            if todostates['in_progress'].search(x[1]):
                if re.search('TODO', x[1]):
                    todolist[i][1] = const.styles['todo'] + x[1] + const.styles['normal']
                else:
                    todolist[i][1] = const.styles['started'] + x[1] + const.styles['normal']
            if x[3].strip() != '':
                todolist[i][3] = const.styles['checkbox'] + x[3] + const.styles['normal']
            # Late tasks should be in all red
            if i in late:
                if i in repeats:
                    todolist[i][4] = ''
                else:
                    todolist[i][4] = const.styles['late'] + x[4].strip() + '\n'
                todolist[i][5] = const.styles['tag'] + x[5].strip().lstrip(':').title() + const.styles['late']
                todolist[i][2] = const.styles['late'] + x[2]

            # Upcoming tasks
            else:
                if x[4].strip() != '':
                    if i in repeats:
                        todolist[i][4] = ''
                    else:
                        todolist[i][4] = const.styles['date'] + x[4].strip() + const.styles['normal'] + '\n'

                    todolist[i][5] = const.styles['tag'] + x[5].strip().lstrip(':').title() + const.styles['normal']# + ':'
                    todolist[i][2] = utils.format_str(todolist[i][2]) + const.styles['normal']

    if not todolist:
        print "No tasks!"
        return

    longest_tag = max([len(x[5]) for x in todolist])
    if longest_tag < 18:
        longest_tag = 18
    for i,x in enumerate(todolist):
        x[5] = x[5] + ' '*(18 - taglengths[i])#len(x[5]))
        print x[4] + '  ' + x[5] + ''.join(x[1:4]) + x[6],
    print

#def colorize():
#-----------------------------------------------------------
# Other functions (to be replaced)
#-----------------------------------------------------------
#def tmp():
#    else:
#        l = listAll(args.file)
#            category = args.category
#            if category == 'all':
#                for x in l: print(x)
#            else:
#                cat_ind = next((i for i, x in enumerate(l) if x.find(category) != -1))
#                cat_ind2 = next((i for i, x in enumerate(l[(cat_ind + 1):len(l)]) if x.find('1m* ') != -1))
#                for x in l[cat_ind:(cat_ind + cat_ind2 + 1)]: print(x)
