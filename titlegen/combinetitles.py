# -*- coding: utf-8 -*-
#!/usr/bin/env python

import csv, os
import json

realtitles = []
with open('./combined_tdcs_data.csv', 'rb') as f:
	reader = csv.reader(f,delimiter=',')
	headers = reader.next()
	for row in reader:
		realtitles.append(row[0].lower())

faketitles = []
with open('./fake_titles.txt', 'rb') as f:
	reader = csv.reader(f,delimiter=',')
	for row in reader:
		faketitles.append(row[0].lower())

titles = realtitles + faketitles
print len(titles)
titles = set(titles)
print len(titles)

data = {'real':[],'fake':[]}
realcount=0
fakecount=0
for title in titles:
	if title != '':
		if title in realtitles:
			data['real'].append(title)
			realcount=realcount+1
		if title in faketitles and title not in realtitles:
			data['fake'].append(title)
			fakecount=fakecount+1

f = open('./titlesdb.json', 'w+')
f.write(json.dumps(data))
f.close()