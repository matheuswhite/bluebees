def check_flag(flag, flag_set):
    return flag[0] in flag_set or flag[1] in flag_set


def find_key(obj_dict: dict, key: str):
    for k in obj_dict.keys():
        if k == key:
            return obj_dict[k]
        elif type(obj_dict[k]) != dict:
            return ''
        else:
            ret = find_key(obj_dict[k], key)
            if type(ret) == dict:
                return ret
    return None


def order(i: int):
    if i % 10 == 1:
        return 'st'
    elif i % 10 == 2:
        return 'nd'
    elif i % 10 == 3:
        return 'rd'
    else:
        return 'th'


class FinishAsync(KeyboardInterrupt):
    pass
