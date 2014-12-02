NUM_VERSION = (2, 3, 1)

import sip
import os
import sys

curpath = os.path.dirname(__file__)
sys.path.append(curpath)

try:
    types = ["QDate", "QDateTime", "QString", "QTextStream", "QTime", "QUrl", "QVariant"]
    for qtype in types:
        sip.setapi(qtype, 2)
except ValueError:
    # API has already been set so we can't set it again.
    pass


def get_git_changeset():
    """Returns the SHA of the current HEAD
    """
    import os
    import subprocess

    full_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    sha = subprocess.check_output(['git', 'rev-parse', '--short','HEAD'], cwd=full_path)
    return sha.split('\n')[0]


def part_string(part, i):
    """Convert a version number part into a string for concatentation.

    Makes the following transformations:
        * Any number into a string:
            1 -> '1'
        * Any tuple into flat concatenated string:
            ('a', 2) -> 'a2'
        * The string 'dev' in to a dvelopment version number:
            dev'-> dev-{SHA}

    Also takes into account whether a prepended dot is required,
    based on the position of the part in the overall string.
    """
    if part == 'dev':
        try:
            sha = get_git_changeset()
        except:
            sha = None

        if sha:
            s = 'dev-{}'.format(sha)
        else:
            s = 'dev'
        if i > 0:
            s = '.' + s
    elif isinstance(part, tuple):
        s = ''.join(str(p) for p in part)
    else:
        s = str(part)
        if i > 0:
            s = '.' + s
    return s

frozen = getattr(sys, "frozen", False)
if frozen:
    with open(os.path.join(curpath, "version.txt"), 'r') as f:
        __version__ = f.read()
else:
    __version__ = "".join(part_string(nv, i) for i, nv in enumerate(NUM_VERSION))

