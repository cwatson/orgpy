from setuptools import setup, find_packages
from os import path
from io import open

setup(
    name = 'orgpyvim',
    version = '0.7.0',
    author = 'Christopher G. Watson',
    author_email = 'cwa135@alum.mit.edu',
    description = 'Python package to get important information from org-mode files',
    url = 'https://github.com/cwatson/orgpyvim',
    classifiers = [
        'Development Status :: 1 - Planning',
        'Programming Language :: Python :: 3.6',
        'Intended Audience :: End Users/Desktop',
        'Operating System :: POSIX :: Linux',
    ],
    license = 'Apache 2.0',
    packages = ['orgpyvim'],#find_packages(),
    keywords = ['orgmode'],
    install_requires = ['setuptools', 'argparse', 'colorama', 'copy', 'datetime', 'os', 're', 'sys', '__future__'],
    python_requires = '>=3.6',
)
