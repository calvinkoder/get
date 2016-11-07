import os
from urllib.parse import urlparse
from ..get import HTML, JSON, Download, TextDownload

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
	def __init__(self, url, orig_name = None, cuck_name = None, use_orig_name = True):
		Download.__init__(self, url)
		self.orig_name = orig_name
		self.cuck_name = cuck_name
		if use_orig_name:
			self.name = orig_name
		else:
			self.name = cuck_name

		self.verifyName()

class Post(HTML):
	file = None
	def __init__(self, post_soup):
		self.soup = post_soup
		self.postId = post_soup.get('id').split('_')[1]
		if 'has-file' in post_soup.get('class'):
			self.files = [File(file_soup) for file_soup in post_soup.find_all(attrs = {'class':'file'})]

		self.text = post_soup.find(attrs = {'class':'body'})

class Thread(HTML, TextDownload):
	local_urls={}
	def __init__(self, url):
		Download.__init__(self, url)
		self.getID(url)
		self.name = self.ID+'.html'
		self.saveText = True

	def getID(self, url):
		parseObj = urlparse(url)
		path = parseObj.path		#/board/res/ID.html
		info = path.split('/')
		self.board = info[1]
		self.ID = info[-1].replace('.html','')

	def req(self, *args, **kwargs):
		HTML.req(self, *args, **kwargs)

		#set current directory as base directory
		base = self.soup.new_tag('base')
		base.attrs['href'] = os.getcwd()
		self.soup.head.append(base)

		self.text = self.soup.get_text()

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
			post = Post(self, post_soup)

	#precondition: self.text exists
	def iter_files(self, use_orig_name = True):
		orig_text = self.text
		for file_soup in self.soup.find_all('div', attrs={'class':'file'}):
			link = ''
			orig_name = ''
			cuck_name = ''

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

			file = File(url, orig_name, cuck_name, use_orig_name)

			self.local_urls[cuck_name] = file.name
			a['href'] = file.name 	#replaces url with local

			yield file

		self.text = self.soup.get_text()

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
			yield Thread(url)