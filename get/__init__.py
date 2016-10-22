import os
import requests
import json
from urllib.parse import urlparse
from bs4 import BeautifulSoup
import get
from get.fs import verifyFilename
import get.units as units

DEFAULT_HEADERS = {'user-agent':'Mozilla/5.0 (Windows NT 6.1; WOW64; rv:18.0) Gecko/20100101 Firefox/49.0'}
DEFAULT_CHUNK_SIZE = 2048

class Resource:
	headers = get.DEFAULT_HEADERS
	defaultMethod = 'GET'
	r = None

	def __init__(self, url):
		self.url = url
		parseObj = urlparse(url)
		self.name = parseObj.path.split('/')[-1]

	def setHeaders(self, **kwargs):
		if not 'headers' in kwargs:
			kwargs['headers'] = self.headers
		return kwargs

	def get(self, **kwargs):
		self.r = requests.get(self.url, **kwargs)

	def post(self, **kwargs):
		self.r = requests.post(self.url, **kwargs)

	def req(self, method = None, **kwargs):
		kwargs = self.setHeaders(**kwargs)
		if not method:
			method = self.defaultMethod
		_req = getattr(Resource, method.lower())
		_req(self, **kwargs)

class Text(Resource):
	text = None
	def req(self, **kwargs):
		Resource.req(self, **kwargs)
		self.text = self.r.text

	def __str__(self):
		return self.text

class JSON(Text):
	JSON = None
	def req(self, **kwargs):
		Text.req(self, **kwargs)
		self.JSON = json.loads(self.text)

class HTML(Text):
	soup = None
	def req(self, **kwargs):
		Text.req(self, **kwargs)
		self.soup = BeautifulSoup(self.text, 'html.parser')

class Download(Resource):
	def dl(self, path='', mkdir=False, dlArgs={}, printProg = False):
		self.req(stream = True, **dlArgs)

		if path and self.name:
			filename = verifyFilename(path, self.name ,mkdir)

			print('Downloading', self.r.url, 'as',filename)
			with open(filename,'wb') as fileObj:
				for chunk in self.dlStream():
					fileObj.write(chunk)

					if printProg:
						print(self.progress, end = '')

			if printProg:
				print()

	def dlStream(self, chunkSize = get.DEFAULT_CHUNK_SIZE):
		self.fileSize = units.Data(0)
		self.downloadedSize = units.Data(0)

		if 'content-length' in self.r.headers:
			self.fileSize=units.Data(int(self.r.headers['content-length']))
		
		self.progress = units.Progress(progress = self.downloadedSize, total = self.fileSize)
		for chunk in self.r.iter_content(chunkSize):
			yield chunk
			self.downloadedSize+=chunkSize
			self.progress.progress = self.downloadedSize

	def verifyName(self):
		while os.path.isfile(self.name):
			_name = self.name.split('.')[0]
			ext = self.name.split('.')[1]
			_name+='-'
			self.name = '.'.join((_name,ext))

class TextDownload(Text, Download):
	def save(self, path='', mkdir=False):
		if path and self.name:
			filename = verifyFilename(path, self.name ,mkdir)

			print('Saving', self.r.url, 'as', filename)
			with open(filename, 'wt') as fileObj:
				fileObj.write(self.text)