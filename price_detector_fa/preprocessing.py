# * imports
from .utils import *
from .hardcoded import (
    # price_anchor_tokens,
    amount_anchor_tokens,
    product_name_anchor_tokens,
)

# * rules
# ** regex replacements
replacements = dict()
replacements[f"\\bهر({or_re(amount_anchor_tokens)})\\b"] = f"هر \\1"
replacements[
    f"""\\b({or_re(product_name_anchor_tokens)})\\s+{or_re([
    'جهانی',
    'بازار',
    'کف بازار',
    'فعلی',
    'حدودی',
    ])}\\b"""
] = f"\\1"

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
    "{}\\s?({})?".format(
        or_re(
            [
                "بیش",
                "کم",
            ]
        ),
        "تر",
    ),
]
regex_token_skip = list(map(re.compile, regex_token_skip))


# * main functions
def preprocess(text: str, disp=False):
    #: @done/Feraidoon implement regex_token_skip
    #: * @done/Hoseini
    #: ** recreate word_tokenize that returns {tokens, indices} (indices should include both start and end indices)
    #: ** do a first pass without any preprocessing and get A from word_tokenize_with_indices
    #: *** do a second pass with word_tokenize after preprocessing and get B
    #: *** match each token in B with the first unmatched token in A that shares its text. (Normalize the A's token's text first.)
    ##

    if disp:
        print(text)
    tokens_raw, indices_raw = word_tokenizer.tokenize_with_indices(text)
    tokens_converted = []
    for token in tokens_raw:
        if token in simple_replacements.keys():
            tokens_converted.append(simple_replacements[token])
        else:
            tokens_converted.append(token)

    for k, v in replacements_compiled.items():
        text = re.sub(k, v, text)

    # text = normalizer.normalize(text)
    #: breaks decimal numbers (like 89.12)

    if disp:
        print(text)
    tokens = word_tokenizer.tokenize_with_indices(text)[0]

    tokens_processed = []
    tokens_indices = []
    curr = 0
    for i, token in enumerate(tokens):
        skip_me = False
        for pattern in regex_token_skip:
            if pattern.match(token):
                skip_me = True
                break
        if skip_me:
            continue

        if token in simple_replacements:
            token = simple_replacements[token]

        try:
            curr = tokens_converted.index(token, curr)
            tokens_processed.append(token)
            tokens_indices.append(indices_raw[curr])
            curr = curr + 1
        except ValueError:
            tokens_processed.append(token)
            tokens_indices.append((-1, -1))

    return tokens_processed, tokens_indices


# * end
