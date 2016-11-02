"""
Alternate to `Versioneer <https://pypi.python.org/pypi/versioneer/>`_ using
`Dulwich <https://pypi.python.org/pypi/dulwich>`_ to sort tags by time from
newest to oldest.

Copy this file (``release_robot.py``) into the package's top folder, import it
into ``__init__.py`` and then set ::

    from release_robot import get_current_version

    __version__ = get_current_version()
    # other dunder classes like __author__, etc.

This example assumes the tags have a leading "v" like "v0.3", and that the
``.git`` folder is in the project folder that containts the package folder.
"""

from dulwich.repo import Repo
import time
import datetime
import os
import re

# CONSTANTS
DIRNAME = os.path.abspath(os.path.dirname(__file__))
PROJDIR = os.path.dirname(DIRNAME)
PATTERN = '[ a-zA-Z_\-]*([\d\.]+[\-\w\.]*)'

def get_recent_tags(projdir=PROJDIR):
    """
    Get list of recent tags in order from newest to oldest and their datetimes.

    :param projdir: path to ``.git``
    :returns: list of (tag, [datetime, commit, author]) sorted from new to old
    """
    project = Repo(projdir)  # dulwich repository object
    refs = project.get_refs()  # dictionary of refs and their SHA-1 values
    tags = {}  # empty dictionary to hold tags, commits and datetimes
    # iterate over refs in repository
    for key, value in refs.iteritems():
        obj = project.get_object(value)  # dulwich object from SHA-1
        # check if object is tag
        if obj.type_name != 'tag':
            # skip ref if not a tag
            continue
        # strip the leading text from "refs/tag/<tag name>" to get "tag name"
        _, tag = key.rsplit('/', 1)
        # check if tag object is commit, altho it should always be true
        if obj.object[0].type_name == 'commit':
            commit = project.get_object(obj.object[1])  # commit object
            # get tag commit datetime, but dulwich returns seconds since
            # beginning of epoch, so use Python time module to convert it to
            # timetuple then convert to datetime
            tags[tag] = [
                datetime.datetime(*time.gmtime(commit.commit_time)[:6]),
                commit.id,
                commit.author
            ]
            
    # return list of tags sorted by their datetimes from newest to oldest
    return sorted(tags.iteritems(), key=lambda tag: tag[1][0], reverse=True)


def get_current_version(pattern=PATTERN, projdir=PROJDIR, logger=None):
    """
    Return the most recent tag, using an options regular expression pattern. The
    default pattern will strip any characters preceding the first semantic
    version. *EG*: "Release-0.2.1-rc.1" will be come "0.2.1-rc.1". If no match
    is found, then the most recent tag is return without modification.

    :param pattern: regular expression pattern with group that matches version
    :param projdir: path to ``.git``
    :param logger: a Python logging instance to capture exception
    :returns: tag matching first group in regular expression pattern
    """
    tags = get_recent_tags(projdir)
    try:
        tag = tags[0][0]
    except IndexError:
        return
    m = re.match(pattern, tag)
    try:
        current_version = m.group(1)
    except (IndexError, AttributeError) as err:
        if logger:
            logger.exception(err)
        return tag
    return current_version


def test_tag_pattern():
    test_cases = {
        '0.3': '0.3', 'v0.3': '0.3', 'release0.3': '0.3', 'Release-0.3': '0.3',
        'v0.3rc1': '0.3rc1', 'v0.3-rc1': '0.3-rc1', 'v0.3-rc.1': '0.3-rc.1',
        'version 0.3': '0.3', 'version_0.3_rc_1': '0.3_rc_1', 'v1': '1',
        '0.3rc1': '0.3rc1'
    }
    for tc, version in test_cases.iteritems():
        m = re.match(PATTERN, tc)
        assert m.group(1) == version
