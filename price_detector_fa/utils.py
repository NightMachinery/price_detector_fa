# * @stdlib
import re

# * icecream
from icecream import ic, colorize as ic_colorize

ic.configureOutput(outputFunction=lambda s: print(ic_colorize(s), flush=True))
# * nltk
from nltk import DependencyGraph

# ** hazm
from hazm import *

normalizer = Normalizer()
stemmer = Stemmer()
lemmatizer = Lemmatizer()
tagger = POSTagger(model="resources/postagger.model")
chunker = Chunker(model="resources/chunker.model")
parser = DependencyParser(tagger=tagger, lemmatizer=lemmatizer)
# * end
