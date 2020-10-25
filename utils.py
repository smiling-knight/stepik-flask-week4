import random

def get_random_set(length: int, max_value: int):
    res = set()
    while len(res) < length:
        res.add(random.randint(1, max_value))
    return res
