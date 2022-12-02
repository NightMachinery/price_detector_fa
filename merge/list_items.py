def list_items(packs, spans):
    outputs = []
    for pack in packs:
        curr = {}
        curr['product_name'] = extracted_show(pack['product_name'])
        curr['product_name_spane'] = (
        spans[pack['product_name'][0][address]][0], spans[pack['product_name'][-1][address]][1])
        curr['product_amount'] = extracted_show(pack['product_amount'])
        curr['product_unit'] = extracted_show(pack['product_unit'])
        curr['price_amount'] = extracted_show(pack['price_amount'])
        curr['price_unit'] = extracted_show(pack['price_unit'])

        outputs.append(curr)

    return outputs