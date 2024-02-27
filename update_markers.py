from pathlib import Path
from pymongo import MongoClient
import json

DIR = str(Path(__file__).parent)
db = MongoClient().flatearth

#Construct markers from any updated messages
updated = False
for message in db.messages.find({'updated': True}):
	updated = True

	x_coord = message['coords'][0]
	z_coord = message['coords'][1] if len(message['coords']) == 2 else message['coords'][2]
	label = message['label']

	#Remove any marker on the specified position, in any dimension.
	db.markers.delete_many({'x': x_coord, 'z': z_coord})

	#Place the new marker
	for dimension in message['emojis']:
		marker = {
			'x': x_coord,
			'z': z_coord,
			'image': 'custom.pin.png',
			'imageAnchor': [0.5, 1],
			'imageScale': 0.3,
			'dimension': dimension,
			'text': f'{label}',
			'textColor': 'white',
			'offsetX': 0,
			'offsetY': 20,
			'font': 'bold 20px Calibri,sans serif',
			'style': 'border: 2px solid red;',
		}
		db.markers.insert_one(marker)

	db.messages.update_one({'_id': message['_id']}, {'$set': {'updated': False}})

#If no messages were updated, do nothing.
if not updated:
	exit()

def process(marker) -> dict:
	del marker['_id']
	return marker

for dimension in ['overworld', 'nether', 'end']:
	text = 'UnminedCustomMarkers = { isEnabled: true, markers: ' + json.dumps([process(i) for i in db.markers.find({'dimension': dimension})], indent = 2) + '}'

	with open(f'/var/www/html/maps/{dimension}/custom.markers.js', 'w') as fp:
		fp.write(text)
