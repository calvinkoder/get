#!/usr/bin/env python3
import argparse
import sys
import os
import fullchan
from get import tor

TOR_DEFAULT_PORT = 1648
proxy = {}
tor_process = None

def dlThread(thread, path, mode = '', proxy = None):
	thread.proxy = args.proxy
	if mode == 'file':
		thread.req()
		thread.dlFiles(path = path, use_orig_name = not args.cuck)
	elif mode == 'archive':
		thread.req()
		thread.archive(path = path)
	else:
		thread.dl(path = path)

path=os.getcwd()

parser=argparse.ArgumentParser()
parser.add_argument('url', metavar = 'url', help = 'Url')
parser.add_argument('-b', action = 'store_true', help = 'Apply settings recursively to all threads in board')
parser.add_argument('-a', action = 'store_true', help = 'Creates an archive of the thread (html, css, files)')
parser.add_argument('-f', action = 'store_true', help = 'Download files only')
parser.add_argument('-cuck', action = 'store_true', help = 'Confirms that you are a cuck and will suffer the consequences')
parser.add_argument('--proxy', default = None, help = 'Set proxy')
parser.add_argument('--https-proxy', default = None, help = 'Set proxy for https')
parser.add_argument('--tor', action = 'store_true', help = 'Connect through Tor')

args=parser.parse_args()

vargs = vars(args)

if 'tor' in vargs:
	port = TOR_DEFAULT_PORT
	proxy_url = 'localhost:{0}'.format(port)
	print('connecting to tor')
	tor_process = tor.start({'SocksPort':str(port)})
	print('connected')
	proxy['http'] = proxy_url
	proxy['https'] = proxy_url
	proxy['ftp'] = proxy_url

if 'proxy' in vargs:
	proxy['http'] = vargs['proxy']
	proxy['https'] = vargs['proxy']
	proxy['ftp'] = vargs['proxy']

if 'https-proxy' in vargs:
	proxy['https'] = vargs['https-proxy']

mode = ''
if args.f:
	mode = 'file'
elif args.a:
	mode = 'archive'

if args.b:
	b = fullchan.Board(args.url)
	b.reqThreads()
	for thread in b.iter_threads():
		dlThread(thread, path, mode = mode, proxy = proxy)
else:
	thread = fullchan.ThreadDownload(args.url)
	dlThread(thread, path, mode = mode, proxy = proxy)

if tor_process:
	tor_process.kill()