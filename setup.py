from setuptools import setup, find_packages
from os import path
from io import open

setup(
    name = 'orgpyvim',
    version = '0.0.1',
    description = 'Python package to get important information from org-mode files',
    license = '',#TODO
    packages = ['orgpyvim'],
    author = 'Christopher G. Watson',
    author_email = 'cwa135@alum.mit.edu',
    classifiers = [
        'Development Status :: 1 - Planning',
        'Programming Language :: Python :: 2.7',
        'Intended Audience :: End Users/Desktop',
        'Operating System :: POSIX :: Linux',
    ],
    keywords = ['orgmode'],
    url = 'https://github.com/cwatson/orgpyvim',
    install_requires = ['setuptools', 'argparse', 'colorama', 'datetime', 'os', 're', 'sys']
)
