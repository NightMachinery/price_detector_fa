# * imports
from .utils import *
from .hardcoded import (
  price_tokens,
  amount_anchor_tokens,
  product_name_anchor_tokens,
  )

# * helper functions
def node_by_text(input_nodes, tokens):
    #: @todo0/Soroosh Use preorder tree traversal. Skip all children when a node matches. Create another function node_by_text_tree, do NOT delete this function.

    addresses = []
    nodes = []

    for i, node in input_nodes.items():
        if node["word"] in tokens:
            addresses.append(i)
            nodes.append(node)

    return dict(addresses=addresses, nodes=nodes)


def lst_str(lst):
    if len(lst) == 0:
        return ""
    else:
        return " ".join(["مقدار: "] + lst)


def nodes_text(nodes):
    return list(map(lambda x: x["word"], nodes))


def extracted_show(extracted):
    return [lst_str(nodes_text(i["nodes"])) for i in extracted]


def extracted_flatten(extracted):
    out = []
    for i in extracted:
        out += i["nodes"]

    return out


# * the cost of the product
def price_extract(dep_graph: DependencyGraph, anchor_tokens=price_tokens):
    nodes = dep_graph.nodes
    price_nodes = node_by_text(nodes, anchor_tokens)

    output = []
    for price_node in price_nodes["nodes"]:
        # ic(price_nodes)

        nums = [price_node]
        accepted = False

        def add(
            node,
            recur_acceptable_tags=(
                "NUM",
                "CONJ",
            ),
            acceptable_tags=("NUM",),
        ):
            nonlocal accepted

            for dep, dep_addresses in node["deps"].items():
                for dep_address in dep_addresses:
                    dep_node = dep_graph.get_by_address(dep_address)
                    # ic(dep, dep_node)

                    if dep_node["tag"] in ("NUM",):
                        accepted = True

                    #: @todo0/Feraidoon If an anchor_token exists in the children of dep_node, do NOT skip it.
                    if dep_node["tag"] in acceptable_tags:
                        nums.append(dep_node)
                        add(
                            dep_node,
                            acceptable_tags=recur_acceptable_tags,
                            recur_acceptable_tags=recur_acceptable_tags,
                        )

        add(price_node)

        if not accepted:
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
def unit_extract(*args, **kwargs):
    return price_extract(*args, **kwargs, anchor_tokens=amount_anchor_tokens)


# * the product name
def subject_extract(
    dep_graph: DependencyGraph,
    stop_nodes=None,  #: @todo/Feraidoon
):
    nodes = dep_graph.nodes.values()

    output = []
    for sbj_node in nodes:
        # ic(sbj_node)
        if (sbj_node["rel"]) not in ("SBJ",):
            continue

        nums = [sbj_node]
        accepted = True

        def add(
            node,
            # recur_acceptable_tags=('NUM',
            #               'CONJ',),
            # acceptable_tags=('NUM',),
        ):
            nonlocal accepted

            for dep, dep_addresses in node["deps"].items():
                for dep_address in dep_addresses:
                    dep_node = dep_graph.get_by_address(dep_address)
                    # ic(dep, dep_node)

                    if True:
                        # if dep_node['tag'] in acceptable_tags:
                        nums.append(dep_node)
                        add(
                            dep_node,
                            # acceptable_tags=recur_acceptable_tags,
                            # recur_acceptable_tags=recur_acceptable_tags,
                        )

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


def cost_extract(dep_graph: DependencyGraph, *args, stop_nodes, node_lst_lst, **kwargs):
    out = cost_extract_by_anchor_tokens(
        dep_graph, *args, stop_nodes=stop_nodes, **kwargs
    )

    if True or len(out) == 0:
        out += cost_extract_by_node_lst_lst(
            dep_graph, *args, node_lst_lst=node_lst_lst, stop_nodes=stop_nodes, **kwargs
        )

    if len(out) == 0:
        out += subject_extract(dep_graph, stop_nodes=stop_nodes)

    #: @todo4/Feraidoon sort 'out' by indices

    return out


def cost_extract_by_anchor_tokens(dep_graph: DependencyGraph, *args, **kwargs):
    anchor_tokens = product_name_anchor_tokens

    nodes = dep_graph.nodes
    cost_nodes = node_by_text(nodes, anchor_tokens)

    return cost_extract_by_nodes(
        dep_graph, *args, **kwargs, cost_nodes=cost_nodes["nodes"]
    )


def cost_extract_by_node_lst_lst(
    *args,
    node_lst_lst,
    **kwargs,
):
    cost_nodes = []
    for extracted in node_lst_lst:
        cost_nodes.append(extracted["nodes"][-1])

    return cost_extract_by_nodes(*args, **kwargs, cost_nodes=cost_nodes)


def cost_extract_by_nodes(dep_graph: DependencyGraph, stop_nodes, cost_nodes):
    nodes = dep_graph.nodes

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


# * putting it all together
def all_extract(dep_graph: DependencyGraph):
    #: @todo6/Hoseini
    price_extracted = price_extract(dep_graph)
    ic(extracted_show(price_extracted))

    unit_extracted = unit_extract(dep_graph)
    ic(extracted_show(unit_extracted))

    nodes = dep_graph.nodes
    stop_nodes = node_by_text(
        nodes,
        [
            #: @todo add more stop words
            "را",
            "در",
            "به",
            "با",
        ],
    )["nodes"]
    stop_nodes += extracted_flatten(price_extracted)
    stop_nodes += extracted_flatten(unit_extracted)

    cost_extracted = cost_extract(
        dep_graph, node_lst_lst=unit_extracted, stop_nodes=stop_nodes
    )
    ic(cost_extracted, extracted_show(cost_extracted))

    return None

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


# * end
