import os
from get.exceptions import InvalidPathException

def verifyFilename(path, name, mkdir = False, overwrite = False):
	if '~' in path:
		path=path.replace('~',os.path.expanduser('~'))

	filename = os.path.join(path,name)
	dirname = os.path.dirname(filename)

	if not os.path.exists(dirname):
		if mkdir:
			os.makedirs(dirname)
		else:
			name = name.replace('/','%47')
			filename = os.path.join(path,name)

	if not overwrite:
		while os.path.isfile(filename):
			name = filename.split('.')[0]
			ext = filename.split('.')[1]
			name += '-'
			filename = '.'.join((name,ext))

	return filename