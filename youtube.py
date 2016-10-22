#!/usr/bin/env python3
import argparse
import os
import json
import threading
from queue import Queue
from subprocess import check_output
from youtube.offliberty import Offurl, Offget
from youtube import Channel

def getVid(url, path, vid = False, name = '', thumb = False):
	o = Offget(url, vid = vid)
	if name:
		o.name = name
	o.getUrl()
	o.dl(path = path, printProg = True)
	if thumb:
		o.ytVid.setInfo()
		o.ytVid.thumb.dl(path = path)

def getVidThreader(q, **kwargs):
	worker = q.get()
	getVid(**kwargs)
	q.task_done()

def getVidAsync(q, **kwargs):
	thread = threading.Thread(target =getVidThreader, args = [q], kwargs = kwargs)
	thread.start()
	q.put(q.qsize())

def getClipboard():
	#requires 'xsel' command
	return check_output(['xsel']).decode('utf-8')

def autoDownload(**kwargs):
	q = Queue()
	threads = []
	kwargs['url'] = ''
	printed = False
	
	while True:
		text = 	getClipboard()
		if text != kwargs['url']:
			kwargs['url'] = text
			if [link for link in ['youtube.com','youtu.be'] if link in text]:
				getVidAsync(q, **kwargs)
		else:
			if not printed:
				print(text, 'is not a valid url')
				printed = True

if __name__ == '__main__':
	parser=argparse.ArgumentParser()
	parser.add_argument('url', metavar = 'url', nargs='?', help = 'Video url')
	parser.add_argument('-V', action = 'store_true', help = 'Download the video instead of audio')
	parser.add_argument('-T', action = 'store_true', help = 'Download thumbnail')
	parser.add_argument('-u', action = 'store_true', help = 'Get the offliberty url only')
	parser.add_argument('-o', default = '', help = 'Specify output file')
	parser.add_argument('-auto', action = 'store_true', help = 'Auto download any urls in clipboard')
	parser.add_argument('-C', action = 'store_true', help = 'Download all videos from channel')

	args=parser.parse_args()
	path=os.getcwd()

	if args.auto:
		autoDownload(path = path, vid = args.V, name =args.o, thumb = args.T)	
	else:
		if args.u:
			o = Offurl(args.url, vid = args.V)
			o.req()
			print(o.text)
			if args.T:
				o.ytVid.thumb.testUrl()
				print(o.ytVid.thumb.url)
		elif args.C:
			channel = Channel(args.url)
			channel.req()
			for vid in channel.iter_vids():
				getVid(vid.url, path = path, vid = args.V, name = args.o, thumb = args.T)
		else:
			getVid(url = args.url, path = path, vid = args.V, name = args.o, thumb = args.T)