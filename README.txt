This is Fafafa, a program that generates RSS feeds from "featured
content of the day"-type things on Wikimedia projects.

For more information, see
http://en.wikipedia.org/wiki/User:Skagedal/Fafafa

fafafa.py is the program itself. Edit it to configure paths and stuff.
Invoke it with ./fafafa.py --help to see options.

do_fafafa.sh is a wrapper script. I've set it up to run every
hour. This means that if there is a problem, for example with
accessing Wikipedia, then it will try again an hour later. However,
due to its caching, it will not download each page more than once.  To
get it to run every hour (I actually run it 5 minutes past, for some
reason), invoke "crontab -e" and write:

# m h  dom mon dow   command
5 * * * * /home/skagedal/fafafa/do_fafafa.sh

That's all, I guess.

Simon Kagedal <skagedal@toolserver.org>
