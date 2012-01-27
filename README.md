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

you'll need to add the following as well to your hgrc file:

    [auth]
	kiln.prefix = https://kilnrepo.kilnhg.com
	kiln.username = tim@kilnorg.com
	kiln.password = keymash

yeah, that's a little gross, but those are the breaks