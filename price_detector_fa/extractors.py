# * imports
from .utils import *
from .hardcoded import (
    price_anchor_tokens,
    amount_anchor_tokens,
    product_name_anchor_tokens,
    subject_stop_words,
)

# * helper functions
def node_children_get(dep_graph: DependencyGraph, node, include_self=True):
    accum = []
    if include_self:
        accum.append(node)

    for dep, dep_addresses in node["deps"].items():
        for dep_address in dep_addresses:
            dep_node = dep_graph.get_by_address(dep_address)

            accum.append(dep_node)
            accum += node_children_get(dep_graph, dep_node, include_self=False)

    return accum


def node_by_text_tree(dep_graph: DependencyGraph, input_nodes, tokens):
    #: @done/Soroosh Use preorder tree traversal. Skip all children when a node matches. sample_15.

    def preorder(node, tokens):
        addresses = []
        nodes = []
        if node["word"] in tokens:
            addresses.append(node["address"])
            nodes.append(node)
        else:
            for dep, dep_addresses in node["deps"].items():
                for dep_address in dep_addresses:
                    dep_node = dep_graph.get_by_address(dep_address)
                    child_nodes = preorder(dep_node, tokens)
                    addresses = addresses + child_nodes["addresses"]
                    nodes = nodes + child_nodes["nodes"]
        return dict(addresses=addresses, nodes=nodes)

    return preorder(input_nodes[0], tokens)


def node_by_text(input_nodes, tokens):
    addresses = []
    nodes = []

    for i, node in input_nodes.items():
        if node["word"] in tokens:
            addresses.append(i)
            nodes.append(node)

    return dict(addresses=addresses, nodes=nodes)


def create_word(word, address=-2):
    return dict(
        nodes=[
            {
                "address": address,
                "word": word,
                "lemma": None,
                "ctag": None,
                "tag": None,
                "feats": None,
                "head": None,
                "deps": defaultdict(list),
                "rel": None,
            }
        ]
    )


def create_YEK(address=-2):
    return dict(
        nodes=[
            {
                "address": address,
                "word": "یک",
                "lemma": None,
                "ctag": None,
                "tag": "NUM",
                "feats": None,
                "head": None,
                "deps": defaultdict(list),
                "rel": None,
            }
        ]
    )


def lst_str(lst):
    if len(lst) == 0:
        return ""
    else:
        return " ".join(["مقدار: "] + lst)


def nodes_text(nodes):
    return list(map(lambda x: x["word"], nodes))


def extracted_show(extracted):
    return [lst_str(nodes_text(i["nodes"])) for i in extracted]


def matching_show(matching, spans):
    #: @todo extract extra fields such as price units
    return {
        "product_name": lst_str(nodes_text(matching["product_name"]["nodes"])),
        "product_name_span": (
            spans[matching["product_name"]["nodes"][0]["address"]][0],
            spans[matching["product_name"]["nodes"][-1]["address"]][1],
        ),
        "product_unit": extracted_show(matching["units"]),
        "product_amount": extracted_show(matching["unit_amounts"]),
        "price_unit": extracted_show(matching["prices"]),
        "price_amount": extracted_show(matching["price_amounts"]),
    }


def extracted_flatten(extracted):
    out = []
    for i in extracted:
        out += i["nodes"]

    return out


def extract(
    dep_graph: DependencyGraph,
    node,
    recur_acceptable_tags=(
        "NUM",
        "CONJ",
    ),
    acceptable_tags=("NUM",),
    anchor_tokens=price_anchor_tokens,
):
    nodes = []
    for dep, dep_addresses in node["deps"].items():
        for dep_address in dep_addresses:
            dep_node = dep_graph.get_by_address(dep_address)
            # print(dep, dep_node)

            #: @done/Feraidoon @test/sample_15 If an anchor_token exists in the children of dep_node, do NOT skip it.
            dep_node_children = node_children_get(dep_graph, dep_node)
            dep_node_children = set(map(lambda n: n["word"], dep_node_children))
            dep_node_children_anchors = dep_node_children & set(anchor_tokens)
            if len(dep_node_children_anchors) > 0 or dep_node["tag"] in acceptable_tags:
                nodes = (
                    nodes
                    + [dep_node]
                    + extract(
                        dep_graph,
                        dep_node,
                        acceptable_tags=recur_acceptable_tags,
                        recur_acceptable_tags=recur_acceptable_tags,
                        anchor_tokens=anchor_tokens,
                    )
                )
    return nodes


def number_extract(nodes):
    number_candidates = []
    for word in sorted(nodes, key=lambda x: x["address"]):
        if word["tag"] in ("NUM", "CONJ"):
            number_candidates.append(word)
    number = []
    last_element_address = -1
    for i, word in enumerate(number_candidates):
        if last_element_address == -1:
            if word["tag"] == "NUM":
                last_element_address = word["address"]
                number.append(word)
        else:
            if word["address"] == last_element_address + 1:
                last_element_address += 1
                number.append(word)
            else:
                break
    #: * trim CONJ at end of number
    last_conj = 0
    for word in reversed(number):
        if word["tag"] == "CONJ":
            last_conj += 1
        else:
            break
    return number[:-last_conj] if last_conj != 0 else number


# * the cost of the product
def price_extract(dep_graph: DependencyGraph, anchor_tokens=price_anchor_tokens):
    anchor_tokens = set(anchor_tokens)

    nodes = dep_graph.nodes
    price_nodes = node_by_text_tree(dep_graph, nodes, anchor_tokens)

    output = []
    for price_node in price_nodes["nodes"]:
        # print(price_nodes)

        nums = [price_node] + extract(
            dep_graph, price_node, anchor_tokens=anchor_tokens
        )

        if not any((dep_node["tag"] == "NUM" for dep_node in nums)):
            continue

        # nums = list(reversed(nums))
        nums = sorted(nums, key=lambda x: x["address"])

        # nums_text = list(map(lambda x: x['word'], nums))
        # nums_addresses = list(map(lambda x: x['address'], nums))

        output.append(
            dict(
                nodes=nums,
                # nodes_text=nums_text,
                # nums_addresses=nums_addresses,
            )
        )

    return output


# * the amount of the product
def amount_extract(*args, **kwargs):
    return price_extract(*args, **kwargs, anchor_tokens=amount_anchor_tokens)


# * the product name
def subject_extract(
    dep_graph: DependencyGraph,
    stop_nodes=None,  #: @done/Feraidoon =sample_13=
):
    nodes = dep_graph.nodes.values()

    if stop_nodes is None:
        stop_nodes = []
    # stop_nodes = [] #: @ablation
    stop_nodes_addresses = list(map(lambda x: x["address"], stop_nodes))

    output = []
    for sbj_node in nodes:
        # print(sbj_node)
        if (sbj_node["rel"]) not in ("SBJ",) or sbj_node[
            "address"
        ] in stop_nodes_addresses:
            continue

        nums = [sbj_node]
        accepted = True

        def add(
            node,
        ):
            nonlocal accepted

            for dep, dep_addresses in node["deps"].items():
                for dep_address in dep_addresses:
                    dep_node = dep_graph.get_by_address(dep_address)
                    # print(dep, dep_node)

                    if dep_address not in stop_nodes_addresses:
                        # print("subject dep added", dep_node)

                        nums.append(dep_node)
                        add(
                            dep_node,
                        )
                    else:
                        # print("subject dep SKIPPED", dep_node)
                        pass

        add(sbj_node)

        if not accepted:
            continue

        nums = sorted(nums, key=lambda x: x["address"])

        output.append(
            dict(
                nodes=nums,
            )
        )

    return output


def product_name_extract(
    dep_graph: DependencyGraph, *args, stop_nodes, node_lst_lst, **kwargs
):
    out = product_name_extract_by_anchor_tokens(
        dep_graph, *args, stop_nodes=stop_nodes, **kwargs
    )

    if True or len(out) == 0:
        out += product_name_extract_by_node_lst_lst(
            dep_graph, *args, node_lst_lst=node_lst_lst, stop_nodes=stop_nodes, **kwargs
        )

    if len(out) == 0:
        out += subject_extract(dep_graph, stop_nodes=stop_nodes)

    #: @done/Feraidoon sort 'out' by indices (see =sample_14=)
    for sbj_group in out:
        end_index = max(map(lambda n: n["address"], sbj_group["nodes"]))
        sbj_group["end_token_index"] = end_index

    out = sorted(
        out,
        key=lambda sbj_group: sbj_group["end_token_index"],
        reverse=False,
    )

    # print(out)

    return out


def product_name_extract_by_anchor_tokens(dep_graph: DependencyGraph, *args, **kwargs):
    anchor_tokens = product_name_anchor_tokens

    nodes = dep_graph.nodes
    cost_nodes = node_by_text_tree(dep_graph, nodes, anchor_tokens)

    return product_name_extract_by_nodes(
        dep_graph, *args, **kwargs, cost_nodes=cost_nodes["nodes"]
    )


def product_name_extract_by_node_lst_lst(
    *args,
    node_lst_lst,
    **kwargs,
):
    cost_nodes = []
    for extracted in node_lst_lst:
        cost_nodes.append(extracted["nodes"][-1])

    return product_name_extract_by_nodes(*args, **kwargs, cost_nodes=cost_nodes)


def product_name_extract_by_nodes(dep_graph: DependencyGraph, stop_nodes, cost_nodes):
    nodes = dep_graph.nodes

    if stop_nodes is None:
        stop_nodes = []
    stop_nodes_addresses = list(map(lambda x: x["address"], stop_nodes))

    output = []
    for node in cost_nodes:
        out_nodes = []
        address = node["address"]
        address_next = address + 1
        while (address_next in nodes) and (address_next not in stop_nodes_addresses):
            n = dep_graph.get_by_address(address_next)  #: returns a node
            out_nodes.append(n)
            address_next = address_next + 1

        if len(out_nodes) == 0:
            continue

        output.append(
            dict(
                nodes=out_nodes,
            )
        )

    return output


def find_matchings(
    dep_graph, prices_extracted, units_extracted, product_names_extracted
):
    matchings = []
    prices, units, product_names = tuple(
        sorted(x.copy(), key=lambda x: x["nodes"][0]["address"])
        for x in (prices_extracted, units_extracted, product_names_extracted)
    )

    while True:
        if len(product_names) == 1:
            matchings.append(
                dict(prices=prices, units=units, product_name=product_names[0])
            )
        if len(product_names) <= 1:
            break

        # find prices before next product_name
        last_related_price_index = -1
        for i, price in enumerate(prices):
            if price["nodes"][0]["address"] < product_names[1]["nodes"][0]["address"]:
                last_related_price_index = i
            else:
                break
        last_related_unit_index = -1
        unit_limit_address = 0
        if last_related_price_index == -1:
            unit_limit_address = product_names[0]["nodes"][0]["address"]
        else:
            unit_limit_address = prices[last_related_price_index]["nodes"][0]["address"]
        for i, unit in enumerate(units):
            if unit["nodes"][0]["address"] < unit_limit_address:
                last_related_unit_index = i
            else:
                break
        matchings.append(
            dict(
                prices=prices[: last_related_price_index + 1],
                units=units[: last_related_unit_index + 1],
                product_name=product_names[0],
            )
        )
        prices, units, product_names = (
            prices[last_related_price_index + 1 :],
            units[last_related_unit_index + 1 :],
            product_names[1:],
        )
    return matchings
    #: return matching regex (from left to right in eng) ( ((unit) object (price)* | object ((unit) price)*)* )


def normalize_matching(matching):
    #: discard out of context parts
    #: @todo elements with distance more than CONTEXT_MAX_LENGTH value than neareset part

    matching = copy.deepcopy(matching)

    #: may break a matching into multiple matchings or change it or remove it, returns a list of matchings
    if len(matching["prices"]) == 0:
        return []

    if len(matching["units"]) == 0:
        matching["units"] = [
            create_YEK(matching["product_name"]["nodes"][0]["address"])
        ]

    if len(matching["units"]) == 1:
        matching["units"] = matching["units"] * len(matching["prices"])

    # match each price with a unit from end
    prices = list(reversed(matching["prices"]))
    units = list(reversed(matching["units"]))
    matched_units_rev = []
    unit_index = 0
    for i in range(len(prices)):
        if unit_index == len(units):
            # populate other prices with "One" unit
            for j in range(i, range(len(prices))):
                matched_units_rev.append(create_YEK(prices[i]["nodes"][0]["address"]))
            break
        if i == (len(prices) - 1):
            # for last price add whatever unit remained
            matched_units_rev.append(units[unit_index])
            unit_index += 1
        else:
            if (
                units[unit_index]["nodes"][0]["address"]
                > prices[i + 1]["nodes"][0]["address"]
            ):
                matched_units_rev.append(units[units_index])
                units_index += 1
            else:
                matched_units_rev.append(create_YEK(prices[i]["nodes"][0]["address"]))

    prices = list(reversed(prices))
    units = list(reversed(matched_units_rev))

    new_unit = {"nodes": number_extract(matching["product_name"]["nodes"])}
    if len(new_unit["nodes"]) > 0:
        changed = False
        for i, unit in enumerate(units):
            if unit["nodes"][0]["word"] == "یک" and len(unit["nodes"]) == 1:
                units[i] = copy.deepcopy(new_unit)
                changed = True
        product_name = list(
            sorted(matching["product_name"]["nodes"], key=lambda x: x["address"])
        )
        if changed:
            for i, word in enumerate(product_name):
                if word["address"] == new_unit["nodes"][-1]["address"]:
                    product_name = product_name[i + 1 :]
                    break
            matching["product_name"]["nodes"] = product_name

    price_amounts = []
    prices_tmp = []
    for price in prices:
        new_unit = {"nodes": number_extract(price["nodes"])}
        if len(new_unit["nodes"]) > 0:
            price_amounts.append(new_unit)
            price_nodes = list(sorted(price["nodes"], key=lambda x: x["address"]))
            for i, word in enumerate(price_nodes):
                if word["address"] == new_unit["nodes"][-1]["address"]:
                    price_nodes = price_nodes[i + 1 :]
                    break
            price["nodes"] = price_nodes
        else:
            price_amounts.append(create_YEK(price["nodes"][0]["address"]))
        prices_tmp.append(price)
    prices = prices_tmp

    unit_amounts = []
    units_tmp = []
    for unit in units:
        new_unit = {"nodes": number_extract(unit["nodes"])}
        if len(new_unit["nodes"]) > 0:
            unit_amounts.append(new_unit)
            unit_nodes = list(sorted(unit["nodes"], key=lambda x: x["address"]))
            for i, word in enumerate(unit_nodes):
                if word["address"] == new_unit["nodes"][-1]["address"]:
                    unit_nodes = unit_nodes[i + 1 :]
                    break
            unit["nodes"] = unit_nodes
        else:
            unit_amounts.append(create_YEK(unit["nodes"][0]["address"]))
        if len(unit["nodes"]) == 0:
            unit = create_word("عدد", unit_amounts[-1]["nodes"][-1]["address"])
        units_tmp.append(unit)
    units = units_tmp

    return [
        dict(
            product_name=matching["product_name"],
            prices=prices,
            price_amounts=price_amounts,
            units=units,
            unit_amounts=unit_amounts,
        )
    ]


# * putting it all together
def all_extract(dep_graph: DependencyGraph, spans, disp=False):
    #: @todo6/Hoseini
    price_extracted = price_extract(dep_graph)
    if disp:
        print(extracted_show(price_extracted))

    unit_extracted = amount_extract(dep_graph)
    if disp:
        print(extracted_show(unit_extracted))

    nodes = dep_graph.nodes
    stop_nodes = node_by_text(
        nodes,
        subject_stop_words,
    )["nodes"]
    stop_nodes += extracted_flatten(price_extracted)
    stop_nodes += extracted_flatten(unit_extracted)

    product_name_extracted = product_name_extract(
        dep_graph, node_lst_lst=unit_extracted, stop_nodes=stop_nodes
    )
    if disp:
        print(
            # product_name_extracted,
            extracted_show(product_name_extracted)
        )
    matchings = find_matchings(
        dep_graph, price_extracted, unit_extracted, product_name_extracted
    )
    matchings_normalized = list(
        itertools.chain.from_iterable(normalize_matching(m) for m in matchings)
    )

    return matchings_normalized

    #: min(len(price), len(objects))
    #:
    #: * @todo0/Soroosh If one price and one object found but no count found,
    #: ** assume the count to be one.
    #: * @todo7/Soroosh If the found len(counts) is less than len(objects),
    #:   then use the indices of the found objects and prices to match the found counts to objects.
    #:   Then assume count one for other unmatched objects.
    #: * @todo/Soroosh after all objects have a matched count, then
    #: ** extract numbers from the objects found, and replace their matched count with the extracted nmber.
    #: *** only do this if the old count is one. Else, throw a warning.
    #: @update/Soroush for matching we assume that object is before pric
    #: * we are able to skip information about change of prices like value of something become cheaper
    #: @update/Soroush matching regex (from left to right in eng) ( ((unit) object (price)* | object ((unit) price)*)* )


# * end
