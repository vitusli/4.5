from functools import reduce
import re
from typing import Union

def dget(data: dict, key: Union[str, list]):
    if type(key) is list:
        return reduce(lambda d, k: d.get(k) if d else None, key, data)
    else:
        return data.get(key)

def dset(data: dict, key: Union[str, list], value):
    if type(key) is list:
        nested = reduce(lambda acc, k: acc.setdefault(k, {}), key[:-1], data)
        nested[key[-1]] = value

    else:
        data[key] = value

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

def rotate_list(list, amount):
    for i in range(abs(amount)):
        if amount > 0:
            list.append(list.pop(0))
        else:
            list.insert(0, list.pop(-1))

    return list

def get_biggest_index_among_names(names):
    if names:
        indexRegex = re.compile(r".*([\d]{3}).*")
        indices = [int(indexRegex.match(name).group(1)) if indexRegex.match(name) else 0 for name in names]

        if indices:
            return max(indices)

def get_ordinal(number: int):
    if number > 0:
        if number == 1:
            return "1st"

        elif number == 2:
            return "2nd"

        elif number == 3:
            return "3rd"
        else:
            return f"{number}th"

    else:
        return "impossible ordinal"

def shorten_float_string(float_str, count=4):
    split = float_str.split('.')

    if len(split) == 2:
        return f"{split[0]}.{split[1][:count].rstrip('0').rstrip('.')}"
    else:
        return float_str
