from __future__ import absolute_import
import re, os, copy
from . import const
from . import utils

__all__ = ['OrgTree', 'orgTreeFromFile']
#===============================================================================
# Class definition for an org "tree"; i.e., a unit of the outline hierarchy
#===============================================================================
class OrgTree:
    """Create an 'OrgTree', which contains the text in an entire org file.

    If there are multiple level-one headings---with a single asterisk---they
    will be stored in the 'children' attribute. The tasks from the children
    will be merged into the 'all' attribute.

    Args:
        orgfile (str): full pathname of the org file
        todostates (dict): dictionary containing the 'in_progress' and
            'completed' TODO keywords
        **kwargs: dictionary containing the command-line arguments

    Attributes:
        all (list): dicts of all active (incomplete) tasks (from all children)
        properties (dict): contains file-wide variables and the CLI options
        children (list): list of 'OrgNode' objects
        data (str): string containing all text in the org file

    Example:
        tree = OrgTree('~/notes.org', todostates, **cli_opts)
    """
    def __init__(self, orgfile, todostates, **kwargs):
        self.properties = {
            'file': orgfile,
            'base': os.path.split(orgfile)[1],
            'todostates': todostates,
            'regex_line': utils.get_parse_string(todostates),
            'cli': kwargs
        }
        if kwargs['tags']: self.properties['tags'] = kwargs['tags']
        if kwargs['states']: self.properties['states'] = kwargs['states']

        f = open(orgfile, 'r')
        self.data = f.read()
        self.check_properties()

        # Parse the file for child nodes, and combine the child lists
        self.children = []
        self.parse()
        self.merge_children()

    def __repr__(self):
        return 'Org file "%s" with %i children' % (self.properties['base'], len(self))

    def __len__(self):
        """Returns the number of child objects."""
        return(len(self.children))

    def check_properties(self):
        """Look for file-wide properties in the org file."""
        matches = const.regex['properties'].findall(self.data)
        if len(matches) > 0:
            for i,x in enumerate(matches):
                self.properties[x[0].lower()] = x[1]

    #-------------------------------------------------------
    # The main class method to parse child nodes
    #-------------------------------------------------------
    def parse(self):
        """Parse org file into a tree or trees if there are multiple roots."""
        lines = self.data.splitlines()
        level = 1
        bounds = []
        for i,x in enumerate(lines):
            if re.search(r'^\*{' + str(level) + '} ', x):
                bounds.append(i)
        bounds.append(len(lines))   # To get the last heading and its content

        trees = []
        for i in range(len(bounds) - 1):
            trees.append(lines[bounds[i]:bounds[i+1]])

        for tree in trees:
            self.children.append(OrgNode('\n'.join(tree), **self.properties))

    def merge_children(self):
        """Join the active tasks from all children."""
        self.all = []
        if self.properties['cli']['colors']:
            for ch in self.children:
                self.all += ch.colored
        else:
            for ch in self.children:
                self.all += ch.active

#===============================================================================
# Class definition for an org "node", a single hierarchy (starting at any level)
#===============================================================================
class OrgNode:
    """Class definition for a single org 'node', or a single hierarchy.

    Args:
        data (str): all text in the node
        properties (dict): the properties from the parent 'OrgTree'

    Attributes:
        data (str): copy of all text in the node
        properties (dict): copy of parent's properties, plus any new ones
        level (int): the # of asterisks of the node
        parsed (list): the 'data', parsed into dict's
        active (list): only "active" TODO's
    """

    def __init__(self, data, **properties):
        self.data = data
        self.properties = properties
        self.update_properties()
        self.level = len(self.data[0]) - len(self.data[0].lstrip('*'))

        # Parse the lines in this node, and get active tasks
        self.parse()
        self.get_active_todos()
        if self.parsed[0]['tag'] != '': self.add_tag()
        if 'category' in self.properties:
            if isinstance(self.properties['category'], list):
                new_cat = [x.title() if x.islower() else x for x in self.properties['category']]
                self.properties.update(category=new_cat)
            else:
                if self.properties['category'].islower():
                    self.properties.update(category=self.properties['category'].title())

            self.add_category()

        # Filter active tasks by agenda, category, or 'todo' state
        self.get_days_to_duedate()
        for p in ['agenda', 'states', 'tags', 'categories']:
            if self.properties['cli'][p]: self.subset_by(p)
        if self.properties['cli']['colors']: self.colorize()

    #-------------------------------------------------------
    # Class methods
    #-------------------------------------------------------
    def update_properties(self):
        """Check if there are any node-specific 'PROPERTIES'."""
        lines = self.data.splitlines()
        bounds = []
        for i,x in enumerate(lines):
            if re.search(':PROPERTIES:', x):
                bounds.append(i)
                break
        for i,x in enumerate(lines):
            if re.search(':END:', x):
                bounds.append(i)
                break
        if len(bounds) < 2: return

        drawer = lines[bounds[0]:bounds[1]]
        drawerlines = [x.split(':')[1:] for x in drawer[1:]]
        properties = {d[0].lower(): d[1].strip() for d in drawerlines}
        for k,v in properties.iteritems():
            if k in self.properties.keys():
                self.properties.update({k: [self.properties[k], v]})
            else:
                self.properties.update({k: v})

    # Main method to parse the raw text into dict's for each line
    #-------------------------------------------------------
    def parse(self):
        """Parse each line in the node into a dictionary.

        The components of the dictionary are:
            - level (the # of asterisks)
            - todostate (TODO, STARTED, DONE, etc.)
            - text (the task's main text)
            - num_tasks (for checkboxes)
            - date
            - tag
            - endline (just a newline character)
        """
        regex_line = self.properties['regex_line']
        matches = [x.groupdict() for x in regex_line.finditer(self.data)]
        for i,d in enumerate(matches):
            if not d['tag']: d['tag'] = ''
        self.parsed = matches

    def get_active_todos(self):
        """Return only the active TODO tasks."""
        date_lines = []
        for _,d in enumerate(self.parsed):
            if d['date'] != '':
                if self.properties['todostates']['in_progress'].search(d['todostate']):
                    date_lines.append(d)
        self.active = date_lines

    # Add category, tag, and # of days to the dicts
    #-------------------------------------------------------
    def add_category(self):
        """Add a category, if present, to each line's 'dict' representation."""
        node_cat = self.properties['category']
        for d in self.active: d.update(category=node_cat)

    def add_tag(self):
        """Add a tag, if present, to each line's 'dict' representation."""
        node_tag = self.parsed[0]['tag']
        for d in self.active:
                d.update(tag=d.get('tag') + node_tag)

    def get_days_to_duedate(self):
        """Update the active TODO dicts with the days left until the due date."""
        for i,d in enumerate(self.active):
            d['days'] = utils.days_until_due(d['date'])

    #---------------------------------------------------------------------------
    # Method for subsetting the active tasks based on CLI options
    #---------------------------------------------------------------------------
    def subset_by(self, type):
        todos = []
        conds = {
            'agenda': "d['days'] < 7",
            'states': "re.search(self.properties['cli']['states'], d['todostate'], re.IGNORECASE)",
            'tags': "re.search(self.properties['cli']['tags'], d['tag'], re.IGNORECASE)"
        }
        if type == 'categories':
            for i,d in enumerate(self.active):
                if isinstance(d['category'], list):
                    catstring = ' '.join(d['category'])
                else:
                    catstring = d['category']
                if re.search(self.properties['cli']['categories'], catstring, re.IGNORECASE):
                    todos.append(d)
        else:
            for i,d in enumerate(self.active):
                if eval(conds[type]): todos.append(d)

        self.active = todos

    #-------------------------------------------------------
    # Apply styles to each active task
    #-------------------------------------------------------
    def colorize(self):
        """Colorize dates, tags, TODO states, and inline text."""
        col = copy.deepcopy(self.active)
        for i,d in enumerate(col):
            # If 'category' is a list, combine them
            if isinstance(d['category'], list):
                col[i].update(category=': '.join(d['category']))

            # Different styles for different todo states
            if re.search('TODO', d['todostate']):
                col[i].update(todostate=const.styles['todo'] + d['todostate'].strip())
            else:
                col[i].update(todostate=const.styles['started'] + d['todostate'].strip())
            col[i]['todostate'] = col[i].get('todostate') + const.styles['normal']

            # Apply diff style depending on due date
            d['tag'] = d['tag'].strip()
            if d['days'] > 0:
                col[i].update(num_tasks=const.styles['checkbox'] + d['num_tasks'] + const.styles['normal'])
                col[i].update(date=const.styles['date'] + d['date'] + const.styles['normal'] + '\n')
                col[i].update(tag=const.styles['tag'] + d['tag'] + const.styles['normal'])
                col[i].update(category=const.styles['tag'] + d['category'] + const.styles['normal'])
                col[i].update(text=utils.format_inline(d['text']) + const.styles['normal'])
            elif d['days'] < 0:
                col[i].update(date=const.styles['late'] + d['date'] + '\n')
                col[i].update(category=const.styles['late'] + d['category'])
                col[i].update(text=const.styles['late'] + d['text'])
            elif d['days'] == 0:
                col[i].update(date=const.styles['today'] + d['date'] + '\n')
                col[i].update(category=const.styles['today'] + d['category'])
                col[i].update(text=const.styles['today'] + d['text'])

        self.colored = col

#-----------------------------------------------------------
# Loop through all 'org' files listed in 'vimrc'
#-----------------------------------------------------------
def orgTreeFromFile(**kwargs):
    """Get list of org files and TODO states from vimrc, read them, and print."""
    todostates = utils.get_todo_states(kwargs['rcfile'])
    if kwargs['file']:
        orgfiles = kwargs['file'].split()
    else:
        orgfiles = utils.get_org_files(kwargs['rcfile'])

    # Loop through the org files
    todolist = []
    for f in orgfiles:
        org = OrgTree(f, todostates, **kwargs)
        todolist += org.all

    # Add dates for the next week even if there are no tasks
    if kwargs['agenda']:
        for d in const.dates_agenda:
            if not any(re.search(d, item) for item in [x['date'] for x in todolist]):
                blank_dict = {
                    'date': const.styles['bright'] + d, 'endline': '\n',
                    'category': '', 'text': '', 'level': '',
                    'num_tasks': '', 'tag': '', 'todostate': ''}
                todolist.append(blank_dict)

    todolist = sorted(todolist, key=lambda d: const.regex['ansicolors'].sub('', d['date']))

    if kwargs['agenda']:
        for i,d in enumerate(todolist):
            todolist[i]['date'] = utils.day_names(d['date'])

    # Remove repeating dates
    repeats = []
    for i,d in enumerate(todolist):
        if i > 0 and todolist[i]['date'] == todolist[i-1]['date']:
            repeats.append(i)
    for i in repeats: todolist[i]['date'] = ''

    # Print
    if not todolist:
        print "No tasks!"; return
    else:
        utils.print_all(todolist, **kwargs)
