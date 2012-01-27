# codereview.py
#
# Copyright Marcos Ojeda <marcos@khanacademy.org> on 2012-01-23.
#
# This software may be used and distributed according to the terms of the
# GNU General Public License version 2 or any later version.


"""create a code review in kiln

This extension allows you to create a code review for a kiln project
from the command line. Real Talk.
"""

import sys
import os
import json
import urllib2
from urllib import urlencode

from mercurial import commands, extensions, help, hg, ui, error
from mercurial import util, scmutil, cmdutil

from pprint import pprint

cmdtable = {}
command = cmdutil.command(cmdtable)

# via https://developers.fogbugz.com/default.asp?W157
def _api(url):
    prefix = ui.ui().config("auth","kiln.prefix")
    return '%s/Api/1.0/%s' % ( prefix, url )

def _slurp(url, params={}, post=False, raw=False):
    params = urlencode(params, doseq=True)
    handle = urllib2.urlopen(url, params) if post else urllib2.urlopen(url + '?' + params)
    content = handle.read()
    obj = content if raw else json.loads(content)
    handle.close()
    return obj

def _token():
    username, password = [ui.ui().config("auth","kiln."+x) for x in ["username","password"]]
    return _slurp(_api('Auth/Login'), dict(sUser=username, sPassword=password))

def _get_user_repos(ui, repo, dest=None):
    repos = repo.ui.configitems("paths")
    user_repos = {}
    for repo in repos:
        user_repos[ repo[0].lower() ] = repo[1]

    if dest:
        if dest.lower() in user_repos:
            repo_path = user_repos[ dest.lower() ]
        else:
            return None
    else:
        if "default-push" in user_repos:
            repo_path = user_repos["default-push"]
        elif "default" in user_repos:
            repo_path = user_repos["default"]
        else:
            return None
    return repo_path.lower()

def _get_reviewers(ui, repo, token, reviewers=[]):
    folks = _slurp(_api("Person"), dict(token=token))

    names = []
    for person in reviewers:
        names += person.split(',')
    if len(names) == 0:
        names += [repo.ui.config("auth","kiln.username")]

    reviewers = [[p for p in folks 
                    if reviewer in p["sName"].lower() or reviewer in p["sEmail"].lower()]
                    for reviewer in names]
    actual_reviewers = []
    for shortname, reviewer in zip(names,reviewers):
        if len(reviewer) > 1:
            choices = ['%s. %s\n' % (x+1, y['sName']) for (x,y) in enumerate(reviewer)]
            ui.status('\nHmm... There are a couple folks named "%s"\n' % shortname)
            [ui.status('%s' % m) for m in choices]
            pick = ui.promptchoice('Which "%s" did you mean?' % shortname, 
                                    ["&"+c for c in choices])
            actual_reviewers += [ reviewer[pick] ]
        else:
            actual_reviewers += reviewer

    return actual_reviewers

def _get_kiln_paths(ui, repo, token):
    prefix = repo.ui.config("auth","kiln.prefix")
    projs = _slurp(_api("Project"), dict(token=token))
    all_repos = {}
    
    for proj in projs:
        repoGroups = proj["repoGroups"]
        for repoGroup in repoGroups:
            repos = repoGroup["repos"]
            for repo in repos:
                components = [repo["sProjectSlug"], repo["sGroupSlug"], repo["sSlug"]]
                repo_path = prefix + "/repo/" + "/".join(components)
                all_repos[ repo_path.lower() ] = repo

    return all_repos

def _make_review(params):
     return _slurp(_api("Review/Create"), params, True)

@command('review|scrutinize',
        [('t', 'title', '', 'use text as default title for code review', 'TITLE'),
         ('c', 'comment', '', 'use text as default comment for code review', 'COMMENT'),
         ('r', 'revs', [], 'revisions for review, otherwise defaults to "tip"', 'REV'),
         ('p', 'people', [], 'people to include in the review, comma separated', 'REVIEWERS'),
         ('e', 'editor', False, 'invoke your editor for default comment')],
         'hg review [-t TITLE] [-e | -c COMMENT] [-p PEOPLE] [-r REV] [repo]')
def review(ui, repo, *dest, **opts):
    """create a code review for some changesets on kiln
    
    Review creates a brand new code review on kiln for a changeset on kiln.
    If no revision is specified, the code review defaults to the most recent
    changeset.
    
    Specify people to peek at your review by passing a comma-separated list
    of people to review your code, by passing multiple -p flags, or both.
      hg review -p tim,alex,ben -p joey
    
    You can specify revisions by passing a hash-range,
      hg review -r 13bs32abc:tip
    or by passing individual changesets
      hg review -r 75c471319a5b -r 41056495619c
    
    Using -e will open up your favorite editor and includes all the changeset
    descriptions for any revisions selected as the code review comment.
    """
    prefix = repo.ui.config("auth","kiln.prefix")
    current_user = repo.ui.config("auth","kiln.username") or repo.ui.config("ui","username")
    if prefix is None:
        ui.warn("In order to work, in your hgrc please set:\n\n")
        ui.warn("[auth]\n")
        ui.warn("kiln.prefix = https://kilnrepo.kilnhg.com\n")
        ui.warn("kiln.username = tim@kilnorg.com\n")
        ui.warn("kiln.password = keymash\n")
        return 0
    
    review_params = {}
    
    changesets = ['tip']
    if opts.get('revs'):
        revs = opts.get('revs')
        changesets = [repo[rev].hex()[:12] for rev in scmutil.revrange(repo, revs)]
    review_params['revs'] = changesets

    comment = opts.get('comment')
    if opts.get('editor'):
        if opts.get('comment'):
            default_comment = opts['comment']
        else:
            changeset_descs = [repo[rev].description() for rev in changesets]
            default_comment = "\n".join(changeset_descs)
        comment = ui.edit(default_comment, current_user)
    if comment:
        review_params['sDescription'] = comment
    
    if opts.get('title'):
        review_params['sTitle'] = opts.get('title')
    
    token = _token()
    review_params['token'] = token
    
    if dest:
        dest = dest[0]
    rev_repo = _get_user_repos(ui, repo, dest)
    if rev_repo:
        all_repos = _get_kiln_paths(ui, repo, token)
        kiln_repo = all_repos[rev_repo]
        review_params["ixRepo"] = kiln_repo["ixRepo"]

    reviewers = _get_reviewers(ui, repo, token, opts.get('people'))
    review_params['ixReviewers'] = [r['ixPerson'] for r in reviewers]
    
    review_status = _make_review(review_params)
    if review_status:
        ui.status("Review created!\n")
        ui.status("%s/Review/%s" % (prefix, review_status['ixReview']))
        return 1
    else:
        return 0
