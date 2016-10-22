import os
import time
import threading
from queue import Queue
from get import HTML, Download
from youtube import Vid
import get.units as units
from get.exceptions import UrlNotFoundException

HOSTNAME = 'http://offliberty.com/'

"""
Requests a conversion from youtube video to audio/video file
input: ytUrl = youtube url
output: res = audio(mp3)/video(mp4) url at offliberty.com
"""
class Offurl(HTML):
	url = HOSTNAME + 'off03.php'
	defaultMethod = 'POST'
	q = Queue()

	def __init__(self, ytUrl, vid = False, getProg = True):
		self.ytVid = Vid(ytUrl)
		self.vid = vid
		self.getProg = getProg

	def setHeaders(self, **kwargs):
		if not 'data' in kwargs:
			data = {'track':self.ytVid.url}
			if self.vid:
				data['video_file'] = 1

			kwargs['data'] = data

		return kwargs

	def post(self, **kwargs):
		HTML.req(self, **kwargs)

		urls = self.soup.find_all(attrs={'class':'download'})
		if urls:
			if self.vid:
				self.text = urls[1].get('href')
			else:
				self.text = urls[0].get('href')
		else:
			raise UrlNotFoundException(self.ytVid.url)

	def req_threader(self):
		worker = self.q.get()
		self.post()
		self.req_done = True
		self.q.task_done()

	def prog_threader(self):
		worker = self.q.get()

		while not self.req_done:				#as long as url not obtained, get progress
			self.progress.req()
			out_text='\r\033[2K{0}'.format(self.progress)
			print(out_text, end='', flush=True)
			time.sleep(0.05)
		print()

		self.q.task_done()

	def req(self):
		print('Getting ', self.ytVid.url, 'as', 'video' if self.vid else 'audio')
		#getting progress while getting url requires threading
		if self.getProg:	
			self.req_done = False
			req_thread = threading.Thread(target = self.req_threader)
			req_thread.daemon = True
			req_thread.start()
			
			self.progress = Progress(self.ytVid.url)
			prog_thread = threading.Thread(target = self.prog_threader)
			prog_thread.daemon = True
			prog_thread.start()

			self.q.put(0)
			self.q.put(1)

			self.q.join()
		else:
			self.post()

"""
Makes an Offurl request and allows for the url to be downloaded
input: ytUrl = youtube url
output: None, use Download.dl() to save the file at url from OffUrl
"""
class Offget(Download):
	def __init__(self, ytUrl, vid = False, name = None, getProg = True):
		self.offurl = Offurl(ytUrl, vid = vid, getProg = getProg)
		self.ytVid = self.offurl.ytVid
		if name:
			self._name = name
			
	def getUrl(self, **kwargs):
		self.offurl.req()
		self.url = self.offurl.text

	@property
	def name(self):
		try:
			return self._name
		except AttributeError:
			raw = self.r.headers['content-disposition']
			start = raw.index('=')						#returns '="filename"'
			self._name = raw[start+2:-1]				#exclude =" from start and " from end
			return self._name

	@name.setter
	def name(self, _name):
		self._name = _name	

"""
Requests conversion progress from Offliberty
Used in conjunction with Offurl
"""
class Progress(HTML, units.Progress):
	dlSite = 'http://offliberty.com/wait.php?url={0}'
	def __init__(self, url, startTime = None):
		HTML.__init__(self, self.dlSite.format(url))
		units.Progress.__init__(self, units.Percent(0), units.Percent(0), startTime)

	def __str__(self, extra = True):
		s = 'Progress: Offstep 1:{0}, Offstep 2:{1}, Time:{2}'
		if self.percents:
			str_list = self.percents +[self.duration()]
			if extra:
				s += ', Rate:{3}, Time Left:{4}'
				str_list += [self.rate(), self.timeLeft()]

			return s.format(*str_list)
		else:
			return 'Wait... Time:{0}'.format(self.duration())

	def req(self):
		HTML.req(self)
		tags = self.soup.find_all('span')
		if tags:
			self.percents = []
			for tag in tags:
				tagVal = tag.contents[0]
				if tagVal == 'Wait':
					tagVal = 0
				else:
					tagVal = int(tagVal.replace('%',''))
				self.percents.append(units.Percent(tagVal))
		else:
			self.percents = None


	def rate(self):
		if self.percents[1].val == 0:
			self.total = units.Percent(100)
		else:
			self.total = units.Percent(200)

		self.progress = self.percents[0] + self.percents[1]
		return units.Progress.rate(self)