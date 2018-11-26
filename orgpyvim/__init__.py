"""
A Python parser for Org mode files.
"""

from __future__ import absolute_import

from .core import Orgfile, orgFromFile
from . import const
from . import utils

__all__ = ['Orgfile', 'orgFromFile']    # Seems equal to the stuff in ".core" above
