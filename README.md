# kiln-review

This is a mercurial extension that allows you to create code reviews on kiln right after you commit/push them on the command line.

The general gist of this is that you can create a code review via `hg` by doing something like this:

    hg review -p tim,alex -p joe

to get alex, tim and joe to review your feature. 

A more full featured example would be this:

    hg review -r ac39a0212:tip -p ben -t "awesome feature" -e

which creates a code review for the range of commits between ac39... and tip. it assigns ben to review the code and sets the title to "awesome feature" and then pops open vim to edit the default comment for the code review.

## Installing

save the `review.py` wherever and in your `~/.hgrc` or just repo/.hg/hgrc add

    [extensions]
	review = /path/to/review.py

you'll need to add the following as well to your hgrc file (use your
actual name and password instead):

    [auth]
	kiln.prefix = https://kilnrepo.kilnhg.com
	kiln.username = tim@kilnorg.com
	kiln.password = keymash

yeah, that's a little gross, but those are the breaks.

you will also need to have the "Mercurial" python package installed:
   http://pypi.python.org/pypi/Mercurial/0.9

or you may `pip install mercurial`

## Using

```
hg review [-t TITLE] [-e | -c COMMENT] [-p PEOPLE] [-r REV] [repo]

aliases: scrutinize

create a code review for some changesets on kiln

    Review creates a brand new code review on kiln for a changeset on kiln. If
    no revision is specified, the code review defaults to the most recent
    changeset.

    Specify people to peek at your review by passing a comma-separated list of
    people to review your code, by passing multiple -p flags, or both. hg
    review -p tim,alex,ben -p joey

    You can specify revisions by passing a hash-range,
      hg review -r 13bs32abc:tip

    or by passing individual changesets
      hg review -r 75c471319a5b -r 41056495619c

    Using -e will open up your favorite editor and includes all the changeset
    descriptions for any revisions selected as the code review comment.

use "hg help -e review" to show help for the review extension

options:

 -t --title TITLE           use text as default title for code review
 -c --comment COMMENT       use text as default comment for code review
 -r --revs REV [+]          revisions for review, otherwise defaults to "tip"
 -p --people REVIEWERS [+]  people to include in the review, comma separated
 -e --editor                invoke your editor for default comment
```