import re
from datetime import datetime, timedelta

from colorama import init, Fore, Back, Style
init(autoreset=True)

# Global variables
#-------------------------------------------------------------------------------
today = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
today_date = '<' + today.strftime('%Y-%m-%d %a') + '>'

styles = {
    'normal': Fore.WHITE + Back.BLACK + Style.NORMAL,
    'bright': Fore.WHITE + Back.BLACK + Style.BRIGHT,
    'todo': Fore.WHITE + Back.RED,
    'doing': Fore.WHITE + Back.BLUE,
    'wait': Fore.BLACK + Back.YELLOW,
    'deadline': Fore.RED + Back.BLACK + Style.BRIGHT,
    'deadline_two': Fore.YELLOW + Back.BLACK + Style.BRIGHT,
    'scheduled': Fore.CYAN + Back.BLACK + Style.BRIGHT,
    'late': Fore.RED + Back.BLACK + Style.BRIGHT,
    'today': Fore.GREEN + Back.BLACK + Style.BRIGHT,
    'later': Fore.BLUE + Back.BLACK + Style.BRIGHT,
    'checkbox': Fore.MAGENTA + Back.BLACK + Style.BRIGHT,
    'code': Fore.GREEN + Style.BRIGHT,
    'category': Fore.MAGENTA + Style.BRIGHT,
    'tag': Fore.YELLOW + Style.BRIGHT,
    'urgent': Fore.WHITE + Back.RED + Style.BRIGHT, # For special "urgent" tags
    'url': Fore.BLUE + Style.BRIGHT,
    'verb': Fore.CYAN + Style.BRIGHT
}

# Regex patterns
#---------------------------------------
inline = {
    'bold': {
        'pattern': re.compile('\*[,\w\s-]+\*'),
        'delim': '*',
        'cols': styles['bright']},
    'code': {
        'pattern': re.compile("=[\._'\w]+="),
        'delim': '=',
        'cols': styles['code']},
    'verb': {
        'pattern': re.compile("~[\._'\w\s]+~"),
        'delim': '~',
        'cols': styles['verb']}
}
date_str = r'[\<\[]' + r'\d{4}-\d{2}-\d{2}' + r' [a-zA-Z]{3}' + r'[\>\]]'
regex = {
    'url': re.compile('\[\[.*\]\]'),
    'date': re.compile(date_str),
    'properties': re.compile(r'#\+([A-Z]*): (.*)\n'),
    'ansicolors': re.compile(r'(\x1b\[[0-9]+[mM])+')
}
