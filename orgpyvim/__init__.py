"""
A Python parser for Org mode files.
"""

from __future__ import absolute_import
from .tree import OrgTree, orgTreeFromFile
from . import const, utils

__all__ = ['OrgTree', 'orgTreeFromFile']    # Seems equal to the stuff in ".core" above
