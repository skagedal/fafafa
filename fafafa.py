#!/usr/bin/python
# -*- coding: UTF-8 -*-
#
#    Copyright 2008 Simon Kågedal
#
#    This file is part of Fafafa.
#
#    Fafafa is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    Fafafa is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with Fafafa.  If not, see <http://www.gnu.org/licenses/>.
#
# http://en.wikipedia.org/wiki/User:Skagedal/Fafafa
#
# This program generates RSS feeds of featured content from Wikimedia projects.
#

import sys
import os
import string
import datetime
import time
import urlparse
import urllib
import httplib
import re
import cPickle
import xml.sax.saxutils
import logging

#
# Settings: Please edit local_settings.py 

settings = {
	'program_name': 'Fafafa',
	'version': '0.9.2',
	'guid': 'http://toolserver.org/~skagedal/feeds/%(id)s-%(year)d-%(month)02d-%(day)02d',
	'entries': 20,
	}

try:
	from local_settings import local_settings
	settings.update(local_settings)
except:
	pass

feeds = {
	# Featured Articles
	'fa': {
		'project': 'en.wikipedia.org',
		'page': 'Wikipedia:Today%%27s_featured_article/%(monthname)s_%(day)d%%2C_%(year)d',
		'rss_title': 'Wikipedia Featured Articles',
		'rss_link': 'http://en.wikipedia.org/wiki/Wikipedia:Today%%27s_featured_article',
	},
	# Picture of the Day
	'potd': {
		'project': 'en.wikipedia.org',
		'page': 'Template:POTD/%(year)d-%(month)02d-%(day)02d',
		'rss_title': 'Wikipedia Picture of the Day',
		'rss_link': 'http://en.wikipedia.org/wiki/Wikipedia:Picture_of_the_day',
	},
	# Selected Anniversaries
	'sa': {
		'project': 'en.wikipedia.org',
		'page': 'Wikipedia:Selected_anniversaries/%(monthname)s_%(day)d',
		'rss_title': 'Wikipedia: On This Day',
		'rss_link': 'http://en.wikipedia.org/wiki/Wikipedia:Selected_anniversaries',
		'no_title': True 
	},
	# Word of the Day
	'wotd': {
		'project': 'en.wiktionary.org',
		'page': 'Wiktionary:Word_of_the_day/%(monthname)s_%(day)d',
		'rss_title': 'Wiktionary Word of the day',
		'rss_link': 'http://en.wiktionary.org/wiki/Wiktionary:Word_of_the_day',
	},
	# Quote of the Day
	'qotd': {
		'project': 'en.wikiquote.org',
		'page': 'Wikiquote:Quote_of_the_day/%(monthname)s_%(day)d,_%(year)d',
		'rss_title': 'Wikiquote: Quote of the day',
		'rss_link': 'http://en.wikiquote.org/wiki/Wikiquote:Quote_of_the_day',
		'no_title': True,
	}
}

# Globals

today_utc = datetime.datetime.utcnow().date()

# Helper to settings
def settings_flag(flag):
	return (flag in settings and settings[flag])

def output_filename():
	return os.path.join(settings['output_dir'], settings['id'] + '.xml')

def cache_filename():
	return os.path.join(settings['cache_dir'], settings['id'] + '_cache.pickle')

# 

months = ["January", "February", "March", "April", "May", "June", "July", "August", "September", "October", "November", "December"]

def get_view_url(date):
	"""Find the URL of featured article of a specific date"""
	return ('http://%s/wiki/%s' % (settings['project'], settings['page'])) % \
		{ 'monthname': months[date.month - 1], 'month': date.month, 'day': date.day, 'year': date.year }

def get_action_url(date, action):
	"""Find the action URL of featured article of a specific date"""
	return ('http://%s/w/index.php?title=%s&action=%s' % (settings['project'], settings['page'], action)) % \
		{ 'monthname': months[date.month - 1], 'month': date.month, 'day': date.day, 'year': date.year }


# Each item should have an unique GUID

def get_guid(date):
	return settings['guid'] % \
		{ 'id': settings['id'], 'monthname': months[date.month - 1], 'month': date.month, 'day': date.day, 'year': date.year }


class MyURLopener(urllib.URLopener):
	"""Subclassing of URLopener - sets "User-agent: ", which Wikipedia requires to be set
	   to something else than the default "Python-urllib"""
	version = settings['program_name'] + "/" + settings['version']

def too_old(date):
	return (today_utc - date).days > settings['entries']
	
# Image size finder

def content_length_and_type(url):
	o = urlparse.urlparse(url)
	conn = httplib.HTTPConnection(o.hostname)
	conn.request("GET", o.path)
	r = conn.getresponse()
	if(r.status != 200):
		raise ConnectionError
	conn.close()
	return (r.getheader("Content-Length"), r.getheader("Content-Type"))

# Caching of HTML from Wikipedia

class CacheItem:
	def __init__(self, html, fetchtime):
		self.html = html
		self.fetchtime = fetchtime
			
class WPCache:

	def __init__(self, cachefilename):
		self.url_opener = MyURLopener()
		self.filename = cachefilename
		if (os.path.exists(cachefilename)):
			file = open(cachefilename)
			self.cache = cPickle.load(file)
			file.close()
		else:
			self.cache = {}
	
	def get_html(self, date):
		if date in self.cache:
			return self.cache[date].html
		else:
			url = get_action_url(date, "render")
			logging.debug("Retreiving %s." % url)
			html = self.url_opener.open(url).read()
			cacheitem = CacheItem(html, time.gmtime())
			self.cache[date] = cacheitem
			return html

	# Weed out old entries, so cache doesn't get big
	def weed_out_old(self):
		self.cache = dict([x for x in self.cache.items() if not too_old(x[0])])
		
	def save(self):
		self.weed_out_old()
		file = open(self.filename, "w")
		p = cPickle.Pickler(file)
		p.dump(self.cache)
		
# Get title of article
#
# ASSUMPTION: 
# * The text inside the first bolded a-tag is the title
# ** If that can't be found, the first bolded text is the title
# *** If that can't be found, the first a-tag is the title
# **** If all else fails, return '(unknown title)'

res_title = [re.compile('<b><a[^>]*>([^<]*)</a>'),
	re.compile('<b>([^<]*)</b>'),
	re.compile('<a[^>]*>([^<]*)</a>')]
def get_title(s):
	if(settings['id'] == 'wotd'):
		return wotd_title(s)
	# Recursive helper function
	def get_title_r(res, s):
		if res == []:
			return '(unknown title)'
		else:
			try:
				m = res[0].search(s)
				s = m.group(1)
				s = s[0].upper() + s[1:]
				return s
			except:
				return get_title_r(res[1:], s)

	return get_title_r(res_title, s)

def wotd_title(s):
	title = re.findall(r'<span id="WOTD-rss-title">(.*?)</span>', s)
	if len(title) == 0:
		raise ParseProblem("WOTD: couldn't find title!")
	return title[0]

def wotd_desc(s):
	desc = re.findall(r'(?s)<div id="WOTD-rss-description">(.*?)</div>', s)
	if len(desc) == 0:
		raise ParseProblem("WOTD: couldn't find description!")
	return desc[0]

def wotd_ogg(s):
	file = re.findall(r'<a href="(http://upload.wikimedia.org/.*?.ogg)', s)
	if len(file) > 0:
		return file[0]
	else:
		return None

def wotd_description(s):
	return '<a href="http://en.wiktionary.org/wiki/%(title)s"><strong>%(title)s</strong></a>\n%(desc)s' % {'title': wotd_title(s), 'desc': wotd_desc(s)}

# Filters content:
# - Removes HTML comments
# - Fixes hrefs
# - For FA, remove everything after "Recently featured: "
# - For SA, remove the documentation div and everything after "More events: "
# - For POTD, only keep the picture and the text next to it
# (these should all fail gracefully)
# Finally:
# - Escapes HTML
#
# ASSUMPTION: internal links (to /wiki/ or /w/) begin with the exact string: 'href="/'
# ASSUMPTION: in-page links begin with 'href="#' 
# ASSUMPTION: documentation div on SA pages start with '<div style="border', and is the only such div. This assumption is likely to change...
# ASSUMPTION: on SA pages, everything from the text '<p>More events: ' is not relevant for RSS feed
# ASSUMPTION: on POTD pages, the content we want is between the first occurence of '<td>' and the last occurence of '</td>'

re_filter_html_comment = re.compile(r'(?s)<!--.*?-->')
re_filter_footer = re.compile(r'(?s)<div class="printfooter">.*')
re_filter_sa_div = re.compile(r'(?si)<div style="border.*?</div>')
re_filter_sa_more = re.compile(r'(?s)<p>More events: .*')
re_filter_fa_recent = re.compile(r'(?s)<p>Recently featured: .*')
re_filter_potd_tablecont = re.compile(r'(?si)<td>.*</td>')
re_filter_qotd_info = re.compile(r'(?si)<p><small>.*</small></p>')
def filter_content(s, page_url):
	s = re_filter_html_comment.sub('', s)
	s = re_filter_footer.sub('', s)
	s = s.replace('href="/', 'href="http://%s/' % settings['project'] )
	s = s.replace('href="#', 'href="%s#' % page_url)
	if settings['id'] == 'fa':
		s = re_filter_fa_recent.sub('', s)
	if settings['id'] == 'sa':
		s = re_filter_sa_div.sub('', s)
		s = re_filter_sa_more.sub('', s)
	if settings['id'] == 'potd':
		tds = re_filter_potd_tablecont.findall(s)
		if (len(tds) == 1):	# should be exactly one match, otherwise we keep the whole content
			s = '<table style="border: none"><tr>' + tds[0] + '</tr></table>'
	if settings['id'] == 'qotd':
		s = re_filter_qotd_info.sub('', s)
	if settings['id'] == 'wotd':
		s = wotd_description(s)

	return xml.sax.saxutils.escape(s)

# Enclosure
def enclosure(date, content):
	if settings['id'] == 'wotd':
		url = wotd_ogg(content)
		try:
			(length, type) = content_length_and_type(url)
		except:
			return "&lt;!-- unable to get file information for enclosure --&gt;"
		return '<enclosure url="%s" length="%s" type="%s" />' % (url, length, type)
	return ""

# Create RSS item

def rss_item(date, content):
	"""date is the date for the item and content is the html"""
	if settings_flag('no_title'):
		title = "%s %d" % (months[date.month - 1], date.day)
	else:
		title = "%s %d: %s" % (months[date.month - 1], date.day, get_title(content))
	return """<item>
<title>%(title)s</title>
<link>%(url)s</link>
<guid>%(guid)s</guid>
<description>%(filtered_content)s</description>
%(enclosure)s
</item>
""" % { 
	'title': xml.sax.saxutils.escape(title), 
	'url': xml.sax.saxutils.escape(get_view_url(date)),
	'guid': xml.sax.saxutils.escape(get_guid(date)),
	'filtered_content': filter_content(content, get_view_url(date)),
	'enclosure': enclosure(date, content)}

# Puts the final RSS together

def rss(items):
	return """<?xml version="1.0" encoding="UTF-8"?>

<rss version="2.0" xmlns:blogChannel="http://backend.userland.com/blogChannelModule" xmlns:atom="http://www.w3.org/2005/Atom">

<channel>
<atom:link href="%(url)s" rel="self" type="application/rss+xml" />
<title>%(rss_title)s</title>
<link>%(rss_link)s</link>
<description>RSS feed of %(rss_title)s, generated from HTML by Fafafa: http://en.wikipedia/wiki/User:Skagedal/Fafafa</description>
<language>en-us</language>
<copyright>GNU Free Documentation License</copyright>
<lastBuildDate>%(build_date)s</lastBuildDate>
<docs>http://blogs.law.harvard.edu/tech/rss</docs>
<webMaster>%(webmaster)s</webMaster>
<generator>%(generator)s</generator>

%(items)s

</channel>
</rss>
""" % {
	'rss_title': settings['rss_title'], 
	'rss_link': settings['rss_link'],
	'webmaster': settings['rss_webmaster'],
	'build_date': time.strftime("%a, %d %b %Y %H:%M:%S +0000", time.gmtime()),
	'items': items, 
	'generator': settings['program_name'] + " " + settings['version'],
	'url': settings['url_base'] + settings['id'] + '.xml' }

def do_feed(feed_id):
	settings.update(feeds[feed_id])
	settings['id'] = feed_id

	cache = WPCache(cache_filename())
	
	one_day = datetime.timedelta(days = 1)
	dates = [today_utc - one_day*x for x in range(settings['entries'])]

	def item(date):
		html = cache.get_html(date) or ''
		return rss_item(date, html)

	# Iterate over the items
	items = string.join([item(date) for date in dates], "")
	the_rss = rss(items)

	# Write to file
	file = open(output_filename(), "w")
	file.write(the_rss)
	file.close()
	
	cache.save()

# Main

def main():
	# Command line parsing
	from optparse import OptionParser
	usage = """usage: %prog [options] feed1 feed2... 
	where feed is one of """ + " ".join(feeds.keys()) + """
	if no feed is specified, all are generated

	alternatively: %prog [options] all"""

	parser = OptionParser(usage=usage, version="0.9.3")
	parser.add_option("-q", "--quiet", action="store_true", dest="quiet", default=False, help="be rather quiet")
	(options, args) = parser.parse_args()

	logging.basicConfig(level=logging.WARNING if options.quiet else logging.DEBUG)

	if args == []:
		args = feeds.keys()
	for f in args:
		if not (f in feeds.keys()):
			print "unknown feed id: %s" % f
			sys.exit(1)
		logging.info("Generating feed '%s'..." % f)
		do_feed(f)

# Useful functions when using from Python shell

def cache():
	return WPCache(cache_filename())

# Don't run if we're imported

if __name__ == '__main__':
	main()

