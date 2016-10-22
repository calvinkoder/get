from urllib.parse import urlparse
import requests
from get import HTML, Download
from get.exceptions import InvalidUrlException

HOSTNAMES = DEFAULT_HOSTNAME, SHORT_HOSTNAME = ('youtube.com/', 'youtu.be/')
MAXRES_DEFAULT_LEN = '1097'

class Vid(HTML):
	def __init__(self, url, name = None):
		self.ID = self.getID(url)
		self.url = url
		self.name = name
		self.thumb = Thumb(self)

	def getID(self, url):
		if DEFAULT_HOSTNAME in url:
			parseObj = urlparse(url)
			query = parseObj.query
			return query[2:]

		elif SHORT_HOSTNAME in url:
			url_parts = url.split(SHORT_HOSTNAME)
			return url_parts[-1]
		else:
			raise InvalidUrlException(url)

	def setInfo(self):
		self.req()
		title = self.soup.find(attrs={'class':'watch-title'})
		if title:
			self.name = title.get('title')

		if not self.thumb.name:
			self.thumb.name = self.name+'.jpg'

class Thumb(Download):
	def __init__(self, vid, name = None):
		self.ID = vid.ID
		self.name = name
		self.maxres = 'http://img.youtube.com/vi/{0}/maxresdefault.jpg'.format(self.ID)
		self.nonmaxres = 'http://img.youtube.com/vi/{0}/0.jpg'.format(self.ID)
		self.url = self.maxres

	def req(self, **kwargs):
		Download.req(self, **kwargs)
		if self.url == self.maxres and self.r.headers['content-length'] == MAXRES_DEFAULT_LEN:
			self.url = self.nonmaxres
			Download.req(self, **kwargs)

class Channel(HTML):
	def __init__(self, url):
		self.url = url

	#precondition: self.req called
	def iter_vids(self):
		for link in self.soup.find_all(attrs={'class':'yt-uix-tile-link'}):
			url = 'https://www.youtube.com{0}'.format(link.get('href'))
			yield Vid(url)