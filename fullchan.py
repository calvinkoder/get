#!/usr/bin/env python3
import argparse
import sys
import os
import fullchan

def dlThread(thread, path, mode = ''):
	if mode == 'file':
		thread.req()
		thread.dlFiles(path = path, use_orig_name = not args.cuck)
	elif mode == 'archive':
		thread.req()
		thread.archive(path = path)
	else:
		thread.dl(path = path, printProg = True)

path=os.getcwd()

parser=argparse.ArgumentParser()
parser.add_argument('url', metavar = 'url', help = 'Url')
parser.add_argument('-b', action = 'store_true', help = 'Apply settings recursively to all threads in board')
parser.add_argument('-a', action = 'store_true', help = 'Creates an archive of the thread (html, css, files)')
parser.add_argument('-f', action = 'store_true', help = 'Download files only')
parser.add_argument('-cuck', action = 'store_true', help = 'Confirms that you are a cuck and will suffer the consequences')

args=parser.parse_args()

mode = ''
if args.f:
	mode = 'file'
elif args.a:
	mode = 'archive'

if args.b:
	b = fullchan.Board(args.url)
	b.reqThreads()
	for thread in b.iter_threads():
		print(thread.url)
		dlThread(thread, path, mode = mode)
else:
	t = fullchan.Thread(args.url)
	dlThread(t, path, mode = mode)