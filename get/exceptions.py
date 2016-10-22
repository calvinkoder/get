class InvalidUrlException(Exception):
	def __init__(self, url):
		Exception.__init__(self, 'Invalid URL: {0}'.format(url))

class UrlNotFoundException(Exception):
	def __init__(self, url):
		Exception.__init__(self, 'URL not found: {0}'.format(url))

class InvalidPathException(Exception):
	def __init__(self, path):
		Exception.__init__(self, 'Invalid path: {0}'.format(path))