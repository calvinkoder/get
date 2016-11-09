import os
from urllib.parse import urlparse
from get import HTML, JSON, Download, TextDownload

HOSTNAME = 'https://8ch.net/'

class CSS(TextDownload):
	def __init__(self, name):
		#convert abs url to rel url
		if name[0] == '/':		
			name = name[1:]
			url = HOSTNAME+name
		else:
			url = name
			parseObj = urlparse(url)
			name = parseObj.path
			name = name[1:]

		Download.__init__(self, url)
		self.name = name
		self.verifyName()

class File(Download):
	orig_name = ''
	cuck_name = ''
	def __init__(self, file_soup, use_orig_name = True):
		fileinfo = file_soup.find(attrs={'class':'fileinfo'})
			
		#orig_name
		unimportant = fileinfo.find(attrs={'class':'unimportant'})
		postfilename = unimportant.find(attrs={'class':'postfilename'})

		#if name is too long, it is placed in the title attribute
		orig_name = postfilename.get('title')
		#otherwise it will be the string
		if not orig_name:
			orig_name = postfilename.string
		#cuck_name
		a = fileinfo.find('a')
		cuck_name = a.get('title')
		if not cuck_name:
			cuck_name = a.string

		url = a.get('href')

		Download.__init__(self, url)

		if use_orig_name:
			self.name = orig_name
		else:
			self.name = cuck_name

		self.verifyName()

class Post(HTML):
	file = None
	op = False
	def __init__(self, post_soup):
		self.soup = post_soup
		self.post_no = self.soup.get('id').split('_')[1]

		self.text = post_soup.find(attrs = {'class':'body'}).get_text()

		if 'op' in self.soup.get('class'):
			self.op = True

		self.poster_id = self.soup.find(attrs = {'class': 'poster_id'})
		if self.poster_id:
			self.poster_id = self.poster_id.contents

		self.name = self.soup.find(attrs = {'class':'name'}).contents
		self.time = self.soup.find('time').dateTime

	def iter_files(self):
		if 'has-file' in self.soup.get('class'):
			for file_soup in self.soup.find_all(attrs = {'class':'file'}):
				yield File(file_soup)

class Thread(HTML, TextDownload):
	local_urls={}
	_post_count = -1

	def __init__(self, soup):
		self.soup = soup

		#set current directory as base directory
		base = self.soup.new_tag('base')
		base.attrs['href'] = os.getcwd()
		self.soup.head.append(base)

		self.text = self.soup.get_text()

	@property
	def post_count(self):
		if self._post_count == -1:
			posts = self.soup.find_all(attrs={'class':'post'})
			self._post_count = len(posts)
		return self._post_count

	#precondition: self.text exists
	def iter_css(self):
		orig_text = self.text
		for stylesheet in self.soup.find_all(attrs={'rel':'stylesheet'}):
			name = stylesheet.get('href')
			css = CSS(name)
			css.verifyName()

			self.local_urls[name] = css.name
			stylesheet['href'] = css.name
			yield css

		self.text = self.soup.get_text()

	def iter_posts(self):
		for post_soup in self.soup.find_all(attrs={'class':'post'}):
			yield Post(post_soup)

	#precondition: self.text exists
	def iter_files(self, use_orig_name = True):
		orig_text = self.text
		for file_soup in self.soup.find_all('div', attrs={'class':'file'}):
			file = File(file_soup, use_orig_name)

			self.local_urls[cuck_name] = file.name
			a['href'] = file.name 	#replaces url with local

			yield file

		self.text = self.soup.get_text()

class ThreadDownload(Thread, TextDownload):
	def __init__(self, url):
		TextDownload.__init__(self, url)
		self.getID(url)
		self.name = self.ID+'.html'

	def getID(self, url):
		parseObj = urlparse(url)
		path = parseObj.path		#/board/res/ID.html
		info = path.split('/')
		self.board = info[1]
		self.ID = info[-1].replace('.html','')

	def req(self, *args, **kwargs):
		HTML.req(self, *args, **kwargs)

		Thread.__init__(self, self.soup)

	def dlCss(self, path, printProg = True):
		for sheet in self.iter_css():
			sheet.dl(path = path, mkdir = True, printProg = printProg)

	def dlFiles(self, path, use_orig_name = True, printProg = True):
		for file in self.iter_files(use_orig_name):
			file.dl(path = path, printProg = printProg)

	def archive(self, path, printProg = False):
		self.dlCss(path = path)
		self.dlFiles(path = path, use_orig_name = False)

		self.save(path = path)
	
class Board(HTML):
	def __init__(self, name):
		self.name = name
		url = HOSTNAME+name
		HTML.__init__(self, url)
		self.threads = JSON(self.url+'/threads.json')

	def reqThreads(self):
		self.threads.req()
		self.threads.JSON = self.threads.JSON[0]['threads']

	def iter_threads(self):
		for thread in self.threads.JSON:
			url = ''.join(str(x) for x in [HOSTNAME, self.name, '/res/', thread['no'], '.html'])
			yield ThreadDownload(url)