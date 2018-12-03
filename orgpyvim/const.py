import re
from datetime import datetime
from datetime import timedelta
from colorama import init, Fore, Back, Style
init(autoreset=True)

# Global variables
#-------------------------------------------------------------------------------
today = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
dates_agenda = []
# %A is for full day name
for i in range(7):
    dates_agenda.append('<' + (today + timedelta(i)).strftime('%Y-%m-%d %a') + '>')

styles = {
    'todo': Fore.WHITE + Back.RED,
    'started': Fore.WHITE + Back.BLUE,
    'waiting': Fore.WHITE + Back.BLUE,
    'normal': Fore.WHITE + Back.BLACK + Style.NORMAL,
    'bright': Fore.WHITE + Back.BLACK + Style.BRIGHT,
    'checkbox': Fore.MAGENTA + Back.BLACK + Style.BRIGHT,
    'date': Fore.BLUE + Back.BLACK + Style.BRIGHT,
    'today': Fore.GREEN + Back.BLACK + Style.BRIGHT,
    'code': Fore.GREEN + Style.BRIGHT,
    'tag': Fore.YELLOW + Style.BRIGHT,
    'late': Fore.RED + Back.BLACK + Style.BRIGHT ,
    'url': Fore.BLUE + Style.BRIGHT,
    'verb': Fore.CYAN + Style.BRIGHT
}

# Regex patterns
#---------------------------------------
inline = {
    'bold': {
        'pattern': re.compile('\*[,\w\s]+\*'),
        'delim': '*',
        'cols': styles['bright']},
    'code': {
        'pattern': re.compile('=[\._\w]+='),
        'delim': '=',
        'cols': styles['code']},
    'verb': {
        'pattern': re.compile('~[\._\w\s]+~'),
        'delim': '~',
        'cols': styles['verb']}
}
regex = {
    'orgfile': re.compile(r'org_agenda_files\s=.*?\[.*?\]', re.DOTALL),
    'todostates': re.compile(r'org_todo_keywords\s=.*?\[.*?\]', re.DOTALL),
    'url': re.compile('\[\[.*\]\]'),
    'date': re.compile('<[0-9].*>'),
    'properties': re.compile(r'#\+([A-Z]*): (.*)\n'),
    'ansicolors': re.compile(r'(\x1b\[[0-9]+[mM])+')
}
