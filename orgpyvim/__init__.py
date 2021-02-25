"""
A Python parser for Org mode files.
"""

__all__ = ['OrgTree', 'orgTreeFromFile']    # Seems equal to the stuff in ".tree" below

from .tree import OrgTree, orgTreeFromFile
from . import const, utils
