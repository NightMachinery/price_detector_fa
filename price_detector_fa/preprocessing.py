# * imports
from .utils import *
from .hardcoded import (
  # price_tokens,
  amount_anchor_tokens,
  product_name_anchor_tokens,
  )

# * helper functions
def or_re(patterns):
    return f"(?:{'|'.join(patterns)})"


# * rules
# ** regex replacements
replacements = dict()
replacements[f"bهر({or_re(amount_anchor_tokens)})b"] = f"هر 1"
replacements[
    f"""b({or_re(product_name_anchor_tokens)})s+{or_re([
    'جهانی',
    'بازار',
    'کف بازار',
    'فعلی',
    'حدودی',
    ])}b"""
] = f"1"

replacements_compiled = dict()
for k, v in replacements.items():
    replacements_compiled[re.compile(k)] = v

# ** simple (fixed string) token replacements
simple_replacements = {
    "هر": "یک",
    "$": "دلار",
}

# ** regex token skips
regex_token_skip = [
    "%s(%s)?".format(
        or_re([
            "بیش",
            "کم",
        ]),
        "تر",
    ),
]
regex_token_skip = list(map(re.compile, regex_token_skip))

# * main functions
def preprocess(text: str):
    #: @todo0/Feraidoon implement regex_token_skip
    #: * @todo5/Hoseini
    #: ** recreate word_tokenize that returns {tokens, indices} (indices should include both start and end indices)
    #: ** do a first pass without any preprocessing and get A from word_tokenize_with_indices
    #: *** do a second pass with word_tokenize after preprocessing and get B
    #: *** match each token in B with the first unmatched token in A that shares its text. (Normalize the A's token's text first.)
    ##
    for k, v in replacements_compiled.items():
        text = re.sub(k, v, text)

    # text = normalizer.normalize(text)
    #: breaks decimal numbers (like 89.12)

    tokens = word_tokenize(ic(text))

    for k, v in simple_replacements.items():
        for i, token in enumerate(tokens):
            if tokens[i] == k:
                tokens[i] = v

    return tokens


# * end
