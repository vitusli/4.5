import bpy

def step_list(current, list, step, loop=True):
    item_idx = list.index(current)

    step_idx = item_idx + step

    if step_idx >= len(list):
        if loop:
            step_idx = 0
        else:
            step_idx = len(list) - 1

    elif step_idx < 0:
        if loop:
            step_idx = len(list) - 1
        else:
            step_idx = 0

    return list[step_idx]

def step_enum(current, items, step, loop=True):
    item_list = [item[0] for item in items]
    item_idx = item_list.index(current)

    step_idx = item_idx + step

    if step_idx >= len(item_list):
        if loop:
            step_idx = 0
        else:
            step_idx = len(item_list) - 1
    elif step_idx < 0:
        if loop:
            step_idx = len(item_list) - 1
        else:
            step_idx = 0

    return item_list[step_idx]

def step_collection(object, currentitem, itemsname, indexname, step):
    item_list = [item for item in getattr(object, itemsname)]
    item_idx = item_list.index(currentitem)

    step_idx = item_idx + step

    if step_idx >= len(item_list):
        step_idx = len(item_list) - 1
    elif step_idx < 0:
        step_idx = 0

    setattr(object, indexname, step_idx)

    return getattr(object, itemsname)[step_idx]

def rotate_list(list, amount):
    for i in range(abs(amount)):
        if amount > 0:
            list.append(list.pop(0))
        else:
            list.insert(0, list.pop(-1))

    return list

def get_cycles_visibility(obj, name):
    return getattr(obj, f'visible_{name}')

def set_cycles_visibility(obj, name, value):
    setattr(obj, f'visible_{name}', value)

def get_indexed_suffix_name(names, name, sep='_', end=''):
    c = 0
    new_name = name + end

    while new_name in names:
        c += 1
        new_name = f"{name}{sep}{str(c).zfill(3)}" + end

    return new_name

def set_name(iddata, name, force=False):
    def get_data_block(iddata):
        idtype = iddata.id_type

        if idtype == 'NODETREE':
            idtype = 'NODE_GROUP'

        return getattr(bpy.data, idtype.lower() + 's', None)

    iddata.name = name

    if force and iddata.name != name:
        print(f"WARNING: forcing name {name} on {iddata}")

        block = get_data_block(iddata)

        if block and (other := block.get(name, None)):
            other.name = f"._TEMPORARY_NAME_{name}"

            iddata.name = name
            other.name = name
