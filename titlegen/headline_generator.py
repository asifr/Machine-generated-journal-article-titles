from collections import defaultdict
from random import randint
from random import random
import os
import itertools
import sys
import re
from titlecase import titlecase
import glob

from timeit import default_timer as timer

# Settings
max_corpus_size = int(os.getenv('MAX_CORPUS_SIZE', 20000))

CHUNK_SIZE = 1000

def pick_next_random_line(file, offset):
    file.seek(offset)
    chunk = file.read(CHUNK_SIZE)
    lines = chunk.split(os.linesep)
    # Make some provision in case yiou had not read at least one full line here
    line_offset = offset + len(os.linesep) + chunk.find(os.linesep)
    return line_offset, lines[1]

def get_n_random_lines(path, n=5):
    lenght = os.stat(path).st_size
    results = []
    result_offsets = set()
    with open(path) as input:
        for x in range(n):
            while True:
                offset, line = pick_next_random_line(input, randint(0, lenght - CHUNK_SIZE))
                if not offset in result_offsets:
                    result_offsets.add(offset)
                    results.append(line)
                    break
    return results

def f7_uniq(seq):
    seen = set()
    seen_add = seen.add
    return [ x for x in seq if x not in seen and not seen_add(x)]

def frag_or_none(fragment):
    if fragment:
        return fragment.fragment
    return ''

def comparison_string(s):
    s = str(s).strip().lower().replace("\"", "")
    re.sub('[^0-9a-zA-Z]+', '', s)
    return s

def includes_any_from_list(string, items_to_check):
    return any(comparison_string(item) in comparison_string(string) for item in items_to_check)

class HeadlineSourcePhrase:
    def __init__(self, phrase, source_id):
        self.phrase = phrase.strip()
        self.source_id = source_id
        self.comparison_string = comparison_string(self.phrase)
    def __eq__(self, other):
        return self.comparison_string == other.comparison_string
    def __hash__(self):
        return self.comparison_string.__hash__()

class HeadlineFragment:
    def __init__(self, source_phrase, fragment):
        self.source_phrase = source_phrase
        self.fragment = fragment
        self.comparison_string = comparison_string(self.fragment)
    def __eq__(self, other):
        return self.comparison_string == other.comparison_string
    def __hash__(self):
        return self.comparison_string.__hash__()
    def __str__(self):
        return self.fragment

class HeadlineResultPhrase:
    def __init__(self):
        self.fragments = []
    def append(self, frag):
        self.fragments.append(frag)

    def merge_fragment_groups(self, fragment_groups):
        fragments = []
        for group in fragment_groups:
            if len(group) > 1:
                fragments.append(HeadlineFragment(group[-1].source_phrase, ' '.join([fragment.fragment for fragment in group])))
            else:
                fragments.append(group[0])
        return fragments

    def reduced_fragments(self):
        fragments = self.fragments
        this_str = str(self)

        # Combine fragments from the same source
        last_source_phrase = None
        current_group = []
        groups = []
        for fragment in fragments:
            if fragment.fragment != '':
                if last_source_phrase != None and last_source_phrase != fragment.source_phrase:
                    groups.append(current_group)
                    current_group = []
                current_group.append(fragment)
                last_source_phrase = fragment.source_phrase
        groups.append(current_group)
        fragments = self.merge_fragment_groups(groups)

        # Combine fragments that start the source phrase
        groups = []
        current_group = []
        sentence = []
        start = 0
        i = 0
        for fragment in fragments:
            sentence.append(fragment.fragment)
            phrase_so_far = ' '.join(sentence[start:])
            if phrase_so_far in fragment.source_phrase.phrase:
                current_group.append(fragment)
            else:
                start = i
                if len(current_group) > 0:
                    groups.append(current_group)
                    current_group = []
                    current_group.append(fragment)
            i += 1
        groups.append(current_group)
        fragments = self.merge_fragment_groups(groups)

        return fragments

    def fragment_hashes(self):
        fragments = []

        char_index = 0
        for frag in self.reduced_fragments():
            hsh = {'index': char_index, 'fragment': titlecase(frag.fragment), 'source_id':frag.source_phrase.source_id, 'source_phrase':frag.source_phrase.phrase}
            fragments.append(hsh)
            char_index += len(frag.fragment)

        return fragments

    def __eq__(self, other):
        return comparison_string(self) == comparison_string(other)
    def __hash__(self):
        return comparison_string(self).__hash__()

    def __str__(self):
        return titlecase(' '.join([fragment.fragment for fragment in self.fragments]).strip())

class HeadlineGenerator:

    def generate(self, sources, depth, seed_word, count = 10):

        self.import_source_phrases(sources, False)
        self.build_map(depth)

        start = timer()

        if HeadlineFragment(None, seed_word) not in self.markov_map.keys():
            print('Seed word ' + seed_word + " not in dictionaries")
            return []

        results = []
        for _ in itertools.repeat(None, count):
            results.append(self.get_sentence(seed_word))

        print "-> sample time " + str(timer() - start)

        return f7_uniq(results)

    # Try to reconstruct a phrase to get the hot metadata
    def reconstruct(self, phrase, sources):

        if not hasattr(self, 'markov_map'):
            print "Building map..."
            self.import_source_phrases(sources, True, phrase.split(" "))
            self.build_map(2)

        sentence = HeadlineResultPhrase()

        map_keys = self.markov_map.keys()
        split_phrase = phrase.split(" ")

        doubled_phrase = []
        i = 0
        while i < len(split_phrase):
            if i + 1 < len(split_phrase):
                doubled_phrase.append(split_phrase[i] + " " + split_phrase[i+1])
                i += 2
            else:
                doubled_phrase.append(split_phrase[i])
                i += 1

        i = 0
        while i < len(doubled_phrase):
            word = doubled_phrase[i]
            # Get the version of this word (with source) that's already in the map
            this_word = map_keys[map_keys.index(HeadlineFragment(None, word))]
            sentence.append(this_word)
            i += 1

            # See if we can find out what the next following word would be
            if i < len(doubled_phrase):
                following_words = self.markov_map[this_word]
                following_words_keys = following_words.keys()
                second_search_fragment = HeadlineFragment(None, doubled_phrase[i])
                if second_search_fragment in following_words:
                    second_word = following_words_keys[following_words_keys.index(second_search_fragment)]
                    sentence.append(second_word)
                    i += 1

        return sentence

    def import_source_phrases(self, sources, dont_window, must_include = []):
        start = timer()

        if not sources:
            # Use all sources
            sources = [os.path.splitext(os.path.basename(f))[0] for f in glob.glob("vendor/headline-sources/db/*.txt")]

        # Import multiple dictionaries
        dir = os.path.dirname(__file__)
        imported_titles = []
        per_dictionary_limit = max_corpus_size / len(sources)
        total = 0
        imported = 0
        for source_id in sources:
            filename = os.path.join(dir, "vendor/headline-sources/db/" + source_id + ".txt")

            archive = open(filename)
            dict_titles = archive.readlines()
            archive.close()
            total += len(dict_titles)

            if not dont_window:
                if len(dict_titles) > per_dictionary_limit:
                    dict_titles = get_n_random_lines(filename, per_dictionary_limit)

            # if len(must_include) > 0:
            #     dict_titles = [x for x in dict_titles if includes_any_from_list(x, must_include)]

            source_phrases = [HeadlineSourcePhrase(headline, source_id) for headline in dict_titles]
            imported += len(source_phrases)

            imported_titles = imported_titles + source_phrases

        self.source_phrases = imported_titles

        print("Imported " + str(imported) + " of " + str(total) + " headlines.")
        print "-> import time " + str(timer() - start)


    def build_map(self, depth):
        start = timer()

        self.depth = depth
        self.markov_map = defaultdict(lambda:defaultdict(int))

        # Generate map in the form word1 -> word2 -> occurences of word2 after word1
        for source_phrase in self.source_phrases[:-1]:
            title = source_phrase.phrase.split()
            if len(title) > self.depth:
                for i in xrange(len(title)+1):
                    a = HeadlineFragment(source_phrase, ' '.join(title[max(0,i-self.depth):i]))
                    b = HeadlineFragment(source_phrase, ' '.join(title[i:i+1]))
                    self.markov_map[a][b] += 1

        # Convert map to the word1 -> word2 -> probability of word2 after word1
        for word, following in self.markov_map.items():
            total = float(sum(following.values()))
            for key in following:
                following[key] /= total


        print "-> map time " + str(timer() - start)

    # Typical sampling from a categorical distribution
    def sample(self, items):
        next_word = ''
        t = 0.0
        for k, v in items:
            t += v
            if t and random() < v/t:
                next_word = k
        return next_word

    def get_sentence(self, seed_word, length_max=140):
        while True:
            sentence = HeadlineResultPhrase()
            next_word = self.sample(self.markov_map[HeadlineFragment(None, seed_word)].items())
            if seed_word:
                keys = self.markov_map.keys()
                sentence.append(keys[keys.index(HeadlineFragment(None, seed_word))])
            while next_word != '':
                sentence.append(next_word)
                tmp_frag_list = [frag_or_none(frag) for frag in sentence.fragments[-self.depth:]]
                tmp_item = HeadlineFragment(None, ' '.join(tmp_frag_list))
                next_word = self.sample(self.markov_map[tmp_item].items())
            str_sentence = comparison_string(str(sentence))
            if any(str_sentence in phrase.comparison_string for phrase in self.source_phrases):
                continue # Prune titles that are substrings of actual titles
            if len(str_sentence) > length_max:
                continue
            return sentence