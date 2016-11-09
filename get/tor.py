import stem.process

def start(config):
	return stem.process.launch_tor_with_config(config)