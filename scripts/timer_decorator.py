import time

def timer(func):
    def wrapper(*args, **kwargs):
        start_time = time.perf_counter()
        result = func(*args, **kwargs)
        end_time = time.perf_counter()
        execution_time = round((end_time - start_time)*1000, 2)
        print(f"Timer: {func.__name__} took {execution_time} ms to run.")
        return result
    return wrapper