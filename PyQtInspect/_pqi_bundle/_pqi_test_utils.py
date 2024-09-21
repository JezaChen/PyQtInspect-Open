# -*- encoding:utf-8 -*-
# ==============================================
# Author: Jeza Chen
# Time: 2023/9/20 19:36
# Description: 
# ==============================================
import functools


def timeit(func):
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        import time
        start = time.time()
        result = func(*args, **kwargs)
        end = time.time()
        print(f'{func.__name__} run time: {end - start}s')
        return result

    return wrapper


def avg_time(func):
    whole_time: int = 0
    count: int = 0

    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        import time
        nonlocal whole_time
        nonlocal count
        start = time.time()
        result = func(*args, **kwargs)
        end = time.time()
        whole_time += end - start
        count += 1
        print(f'{func.__name__} avg run time: {whole_time / count}s, call count: {count}')
        return result

    return wrapper
