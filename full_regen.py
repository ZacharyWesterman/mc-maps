#!/usr/bin/env python3
import subprocess
import json
from pathlib import Path

#Read config and make sure it has all the fields we need
DIR = str(Path(__file__).parent)
with open(f'{DIR}/config.json', 'r') as fp:
	config = json.load(fp)

	failed = False
	for i in ['download_link', 'world']:
		if i not in config:
			print(f'ERROR: config.json missing value "{i}".')
			failed = True

	if failed: exit(1)

	for i in ['name', 'seed', 'location', 'generate_range']:
		if i not in config['world']:
			print(f'ERROR: config.json missing value "world.{i}".')
			failed = True

	if failed: exit(1)

#Check for lock
#We DO NOT want this to run multiple times at once!!
try:
	with open('.REGEN', 'r') as fp:
		exit(0)
except:
	pass

#Create lock
with open('.REGEN', 'w') as fp:
	fp.write('')

try:
	#Parse index.html and place result in web root
	with open(f'{DIR}/index.html', 'r') as fp:
		text = fp.read()

		loc = 0
		prevloc = 0
		endloc = 0
		newtext = ''
		while (loc := text.find('{{', prevloc)) > -1:
			newtext += text[prevloc:loc]

			endloc = text.find('}}', loc)
			if endloc == -1:
				newtext += text[loc::]
				break

			expr = text[loc+2:endloc]
			value = config
			for key in expr.split('.'):
				if type(value) is not dict:
					value = None
					break
				value = value.get(key)

			newtext += str(value)
			prevloc = endloc + 2

		newtext += text[endloc+2::]

		with open('/var/www/html/index.html', 'w') as out:
			out.write(newtext)

	#Download uNmINeD if it doesn't already exist
	if not Path(f'{DIR}/unmined').exists():
		subprocess.call(['wget', config['download_link'], '-O', 'unmined.tar.gz'], cwd = DIR)
		subprocess.call(['tar', 'xzf', 'unmined.tar.gz'], cwd = DIR)
		Path(f'{DIR}/unmined.tar.gz').unlink()

		for f in Path(f'{DIR}/').glob('unmined-*'):
			subprocess.call(['mv', str(f), str(f.parent / 'unmined')], cwd = DIR)
			break

	#Copy world folder locally so we can work on it.
	location = config['world']['location']
	subprocess.call(['rsync', '-a', f'{location}/worlds', '.', '--delete', '--info=progress2'], cwd = DIR)

	#Generate maps from world folders
	gen_range = ':'.join(str(i) for i in config['world']['generate_range'])
	for i in ['overworld', 'nether', 'end']:
		subprocess.call(['./generate', i, gen_range], cwd = DIR) #A good range is -5:5, but it takes a while to run.

	#Create FlatEarth.mcworld file
	subprocess.call(['zip', 'FlatEarth.zip', config["world"]["name"], '-r'], cwd = f'{DIR}/worlds')
	subprocess.call(['mv', 'FlatEarth.zip', '/var/www/html/FlatEarth.mcworld'], cwd = f'{DIR}/worlds')

except Exception as e:
	print(f'ERROR: {e}')

#Release lock
Path('.REGEN').unlink(missing_ok=True)
