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
    'normal': Fore.WHITE + Back.BLACK + Style.NORMAL,
    'bright': Fore.WHITE + Back.BLACK + Style.BRIGHT,
    'checkbox': Fore.MAGENTA + Style.BRIGHT,
    'date': Fore.BLUE + Style.BRIGHT,
    'today': Fore.GREEN + Style.BRIGHT,
    'code': Fore.GREEN + Style.BRIGHT,
    'tag': Fore.YELLOW + Style.BRIGHT,
    'late': Fore.RED + Style.BRIGHT ,
    'url': Fore.BLUE + Style.BRIGHT,
    'file': Fore.CYAN + Style.BRIGHT
}

# Regex patterns
#---------------------------------------
patterns = {
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
        'cols': styles['file']}
}
urlpattern = re.compile('\[\[.*\]\]')
datepattern = re.compile('<[0-9].*>')
catpattern = re.compile(r'#\+CATEGORY:.*')
titlepattern = re.compile(r'\n#\+TITLE:.*')
ansicolors = re.compile(r'(\x1b\[[0-9]+[mM])+')
