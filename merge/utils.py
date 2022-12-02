# * @stdlib
from __future__ import unicode_literals
import re, codecs

#hardcoded tokens
from .hardcoded import (
    amount_anchor_tokens,
    product_name_anchor_tokens,
)

# * icecream
from icecream import ic, colorize as ic_colorize

ic.configureOutput(outputFunction=lambda s: print(ic_colorize(s), flush=True))
# * nltk
from nltk import DependencyGraph

# ** hazm
from hazm import *

# * helper functions
def or_re(patterns):
    return f"(?:{'|'.join(patterns)})"


#revision of Hazm WordTokenizer
class WordTokenizer_with_indices(WordTokenizer):
    def __init__(self, join_verb_parts=True, separate_emoji=False, replace_links=False, replace_IDs=False,
                 replace_emails=False, replace_numbers=False, replace_hashtags=False):
        super(WordTokenizer_with_indices, self).__init__(join_verb_parts, separate_emoji, replace_links, replace_IDs,
                                                         replace_emails, replace_numbers, replace_hashtags)

        # revising pattern such thet the module would not break abbreviated words (e.g. ام.دی.اف)
        self.pattern = re.compile(r'([؟!\?]+|\d[\d\.:\/\\]+\d|[\w+.]+\w+|[:\.،؛»\]\)\}"«\[\(\{])')

    # returns each token with its span in the sentence
    def tokenize_with_indices(self, sent):
        space_added = re.sub(f"\\bهر({or_re(amount_anchor_tokens)})\\b", f"هر \\1", sent)
        tokens = self.tokenize(space_added)
        indices = []
        curr = 0
        for token in tokens:
            curr = sent.find(token, curr)
            indices.append((curr, curr + len(token)))
            curr += len(token)
        return tokens, indices


#returns a dictionary of span of each node in dependency graph
def find_spans (dep_graph, token_indices):
    spans = {}
    for key, node in dep_graph.nodes.items():
        if key>0:
            spans[key] = token_indices[node['address'] - 1]
    return spans

word_tokenizer = WordTokenizer_with_indices()
normalizer = Normalizer()
stemmer = Stemmer()
lemmatizer = Lemmatizer()
tagger = POSTagger(model="resources/postagger.model")
chunker = Chunker(model="resources/chunker.model")
parser = DependencyParser(tagger=tagger, lemmatizer=lemmatizer)
# * end
