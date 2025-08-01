from wrapt import FunctionWrapper


def f(a: bool, b: str) -> int:
    return 1


def standard_wrapper(wrapped, instance, *args, **kwargs):
    pass


f1 = FunctionWrapper(f, standard_wrapper)

reveal_type(f1)

result1a: int = f1(True, "test")
result1b: str = f1(1, None)


def catch_all_wrapper(*args, **kwargs):
    pass


f2 = FunctionWrapper(f, catch_all_wrapper)

reveal_type(f2)

result2a: int = f2(True, "test")
result2b: str = f2(1, None)
