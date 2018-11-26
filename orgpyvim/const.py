import re
from datetime import datetime
from datetime import timedelta
from colorama import init, Fore, Back, Style
init(autoreset=True)

# Global variables
#-------------------------------------------------------------------------------
today = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
styles = {
    'todo': Fore.WHITE + Back.RED + Style.BRIGHT,
    'started': Fore.BLUE + Style.BRIGHT,
    'normal': Fore.WHITE + Back.BLACK + Style.NORMAL,
    'checkbox': Fore.MAGENTA + Style.BRIGHT,
    'date': Fore.GREEN + Style.BRIGHT,
    'tag': Fore.YELLOW + Style.BRIGHT,
    'late': Style.BRIGHT + Fore.RED,
    'url': Fore.BLUE + Style.BRIGHT,
    'file': Fore.CYAN + Style.BRIGHT
}

# Regex patterns
#---------------------------------------
patterns = {
    'bold': {
        'pattern': re.compile('\*[,\w\s]+\*'),
        'delim': '*',
        'cols': Style.BRIGHT},
    'code': {
        'pattern': re.compile('=[\._\w]+='),
        'delim': '=',
        'cols': styles['date']},
    'verb': {
        'pattern': re.compile('~[\._\w\s]+~'),
        'delim': '~',
        'cols': styles['file']}
}
urlpattern = re.compile('\[\[.*\]\]')
datepattern = re.compile('<[0-9].*>')
catpattern = re.compile(r'#\+CATEGORY:.*')
titlepattern = re.compile(r'\n#\+TITLE:.*')
