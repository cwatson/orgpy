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
    will be stored in the 'children' list attribute.

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

        # Parse the file for child nodes
        self.children = []
        self.parse()

        # Combine the parsed (and colored) child lists
        self.merge_children()

    def __repr__(self):
        return 'Org file "%s" with %i children' % (self.properties['base'], len(self))

    def __len__(self):
        """Returns the number of child objects."""
        return(len(self.children))

    def check_properties(self):
        """Look for file-wide properties in the org file."""
        matches = re.findall(r'#\+([A-Z]*): (.*)\n', self.data)
        if len(matches) > 0:
            for i,x in enumerate(matches):
                self.properties[x[0].lower()] = x[1]

    #-------------------------------------------------------
    # The main class method to parse out child nodes
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
        all_tasks = []
        if self.properties['cli']['colors']:
            for ch in self.children:
                all_tasks += ch.colored
        else:
            for ch in self.children:
                all_tasks += ch.active

        self.all = all_tasks

#===============================================================================
# Class definition for an org "node", a single hierarchy (starting at any level)
#===============================================================================
class OrgNode:
    """Class definition for a single org 'node', or a single hierarchy."""
    def __init__(self, data, **properties):
        self.data = data
        self.properties = properties
        self.update_properties()
        self.level = len(self.data[0]) - len(self.data[0].lstrip('*'))

        # Parse the lines in this node, and get active tasks
        self.parse()
        self.get_active_todos()
        if 'category' in self.properties: self.add_category()

        # Filter active tasks by agenda, category, or 'todo' state
        self.get_days_to_duedate()
        if self.properties['cli']['agenda']: self.subset_agenda()
        if self.properties['cli']['states']: self.subset_states()
        if self.properties['cli']['tags']: self.subset_tags()
        if self.properties['cli']['categories']: self.subset_categories()
        if self.properties['cli']['colors']: self.colorize()

    #-------------------------------------------------------
    # Class methods
    #-------------------------------------------------------
    def get_header(self):
        """Return the node's header text."""
        return self.data[0]

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

    # Methods parsing, filtering, and/or changing the active todo list
    #-------------------------------------------------------
    def parse(self):
        regex_line = self.properties['regex_line']
        matches = [x.groupdict() for x in regex_line.finditer(self.data)]
        for i,d in enumerate(matches):
            if not d['tag']: d['tag'] = ''
        self.parsed = matches

    def get_active_todos(self):
        date_lines = []
        for _,d in enumerate(self.parsed):
            if d['date'] != '':
                if self.properties['todostates']['in_progress'].search(d['todostate']):
                    date_lines.append(d)

        self.active = date_lines

    def add_category(self):
        """Add a category, if present, to each line's 'dict' representation."""
        node_cat = self.properties['category']
        for i,d in enumerate(self.active):
            d.update(category=node_cat)

    def get_days_to_duedate(self):
        """Update the active TODO's with the days left until the due date."""
        for i,d in enumerate(self.active):
            d['days'] = utils.days_until_due(d['date'])

    def subset_agenda(self):
        """Subset the active todos if the 'agenda' option is specified."""
        todos = []
        for i,d in enumerate(self.active):
            if d['days'] < 7:
                todos.append(d)

        self.active = todos

    def subset_states(self):
        """Subset the active todos if the 'states' option is specified."""
        todos = []
        for i,d in enumerate(self.active):
            if re.search(self.properties['cli']['states'], d['todostate'], re.IGNORECASE):
                todos.append(d)

        self.active = todos

    def subset_tags(self):
        """Subset the active todos if the 'tags' option is specified."""
        todos = []
        for i,d in enumerate(self.active):
            if re.search(self.properties['cli']['tags'], d['tag'], re.IGNORECASE):
                todos.append(d)

        self.active = todos

    def subset_categories(self):
        """Subset the active todos if the 'categories' option is specified."""
        todos = []
        for i,d in enumerate(self.active):
            if isinstance(d['category'], list):
                catstring = ' '.join(d['category'])
            else:
                catstring = d['category']
            if re.search(self.properties['cli']['categories'], catstring, re.IGNORECASE):
                todos.append(d)

        self.active = todos

    #-------------------------------------------------------
    # Apply styles to each active task
    #-------------------------------------------------------
    def colorize(self):
        """Colorize dates, tags, todo states, and inline text."""
        col = copy.deepcopy(self.active)
        for i,d in enumerate(col):
            # If 'category' is a list, combine them
            if isinstance(d['category'], list):
                col[i].update(category=':'.join(d['category']))

            # Different styles for different todo states
            if re.search('TODO', d['todostate']):
                col[i].update(todostate=const.styles['todo'] + d['todostate'].strip() + const.styles['normal'])
            else:
                col[i].update(todostate=const.styles['started'] + d['todostate'].strip() + const.styles['normal'])
            col[i]['todostate'] = col[i].get('todostate')

            # Apply diff style depending on due date
            if d['days'] > 0:
                col[i].update(num_tasks=const.styles['checkbox'] + d['num_tasks'] + const.styles['normal'])
                col[i].update(date=const.styles['date'] + d['date'] + const.styles['normal'] + '\n')
                col[i].update(tag=const.styles['tag'] + d['tag'].strip().lstrip(':').title() + const.styles['normal'])
                col[i].update(category=const.styles['tag'] + d['category'].strip().lstrip(':').title() + const.styles['normal'])
                col[i].update(header=utils.format_inline(d['header']) + const.styles['normal'])
            else:
                if d['days'] < 0:
                    col[i].update(date=const.styles['late'] + d['date'] + '\n')
                    col[i].update(tag=const.styles['late'] + d['tag'].strip().lstrip(':').title())
                    col[i].update(category=const.styles['late'] + d['category'].strip().lstrip(':').title())
                    col[i].update(header=const.styles['late'] + d['header'])
                elif d['days'] == 0:
                    col[i].update(date=const.styles['today'] + d['date'] + '\n')
                    col[i].update(tag=const.styles['today'] + d['tag'].strip().lstrip(':').title())
                    col[i].update(category=const.styles['today'] + d['category'].strip().lstrip(':').title())
                    col[i].update(header=const.styles['today'] + d['header'])

        self.colored = col

def orgTreeFromFile(**kwargs):
    if kwargs['file']:
        orgfiles = kwargs['file'].split()
    else:
        orgfiles = utils.get_org_files(kwargs['rcfile'])

    todostates = utils.get_todo_states(kwargs['rcfile'])

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
                    'date': const.styles['bright'] + d,
                    'category': '',
                    'endline': '\n',
                    'header': '',
                    'level': '',
                    'num_tasks': '',
                    'tag': '',
                    'todostate': ''
                }
                todolist.append(blank_dict)

    todolist = sorted(todolist, key=lambda d: const.ansicolors.sub('', d['date']))

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
        print_all_dict(todolist, **kwargs)

def print_all_dict(list_, **kwargs):
    """Print the todo list lines, padding the columns."""
    tag_lens = []; state_lens = []
    for i,d in enumerate(list_):
        state_lens.append(len(const.ansicolors.sub('', d['todostate'])))
        tag_lens.append(len(const.ansicolors.sub('', d['category'])))

    longest_state = max(state_lens)
    if kwargs['agenda']:
        maxdatelen = 22     # Date string includes full day name
    else:
        maxdatelen = 18
    longest_tag = max(maxdatelen, max(tag_lens))
    utils.print_header(**kwargs)
    for i,d in enumerate(list_):
        d['todostate'] = d['todostate'] + ' '*(longest_state + 2 - state_lens[i])
        d['category'] = d['category'] + ' '*(longest_tag + 1 - tag_lens[i])
        print re.sub('<|>', '', d['date']) + '  ' + d['category'] + \
            d['todostate'] + ' ' + d['header'] + d['num_tasks']
