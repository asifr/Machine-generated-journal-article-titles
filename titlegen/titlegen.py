# -*- coding: utf-8 -*-
#!/usr/bin/env python

import csv, os
import nltk

titles = []

with open('./combined_tdcs_data.csv', 'rb') as f:
		reader = csv.reader(f,delimiter=',')
		headers = reader.next()
		for row in reader:
			titles.append(row[0])

tokenizer = nltk.tokenize.RegexpTokenizer(r'\w+|[^\w\s]+')

content_text = ' '.join(t for t in titles)
tokenized_content = tokenizer.tokenize(content_text)
content_model = nltk.NgramModel(3, tokenized_content)

# starting_words = content_model.generate(100)[-2:]
words_to_generate = 10000
content = content_model.generate(words_to_generate)
print ' '.join(content)