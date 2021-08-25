from itertools import islice


def group_elements(lst, chunk_size):
    lst = iter(lst)
    return iter(lambda: tuple(islice(lst, chunk_size)), ())
