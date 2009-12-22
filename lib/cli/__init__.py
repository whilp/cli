"""The ``cli`` package is a framework for making simple, correct command
line applications in Python. With ``cli``, you can quickly add standard 
`logging`_, `testing`_, `profiling`_ to your CLI apps. To make it easier
to do the right thing, ``cli`` wraps all of these tools into a single,
consistent application interface.

.. _logging:    http://docs.python.org/library/logging.html
.. _testing:    http://docs.python.org/library/unittest.html
.. _profiling:  http://docs.python.org/library/profile.html
"""

__project__ = "pyCLI"
__version__ = "0.3.4"
__package__ = "cli"
__description__ = "Simple, Object-Oriented approach to Python CLI apps"
__author__ = "Will Maier"
__author_email__ = "will@m.aier.us"
__url__ = "http://code.lfod.us/cli"

# See http://pypi.python.org/pypi?%3Aaction=list_classifiers.
__classifiers__ = [] 
__keywords__ = "command line application framework"

__requires__ = []

# The following is modeled after the ISC license.
__copyright__ = """\
2009 Will Maier <will@m.aier.us>

Permission to use, copy, modify, and distribute this software for any
purpose with or without fee is hereby granted, provided that the above
copyright notice and this permission notice appear in all copies.

THE SOFTWARE IS PROVIDED "AS IS" AND THE AUTHOR DISCLAIMS ALL WARRANTIES
WITH REGARD TO THIS SOFTWARE INCLUDING ALL IMPLIED WARRANTIES OF
MERCHANTABILITY AND FITNESS. IN NO EVENT SHALL THE AUTHOR BE LIABLE FOR
ANY SPECIAL, DIRECT, INDIRECT, OR CONSEQUENTIAL DAMAGES OR ANY DAMAGES
WHATSOEVER RESULTING FROM LOSS OF USE, DATA OR PROFITS, WHETHER IN AN
ACTION OF CONTRACT, NEGLIGENCE OR OTHER TORTIOUS ACTION, ARISING OUT OF
OR IN CONNECTION WITH THE USE OR PERFORMANCE OF THIS SOFTWARE.
"""

__todo__ = """\
* cli.app:
    * more tests
    * re-add config support (via ParameterHandler)
    * add Windows registry/OS X plist support (sekhmet)
* cli.test:
    * doctest support
    * {setup,teardown}_module support?
    * verify py.test hook functionality
    * tests
"""

# Import API-level elements.
from app import *
