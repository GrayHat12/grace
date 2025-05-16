import time
import inspect
from collections import defaultdict

from typing_extensions import ParamSpec
from typing import TypeVar, Callable, Literal, Union, get_args, overload

from .models import LatencyStat, UnitInfo

P = ParamSpec('P')
R = TypeVar('R')

TRACKING_KEYS_TYPE = Literal["FUNCTION", "CALLS", "AVG LAT (ms)", "MAX LAT (ms)", "MIN LAT (ms)", "TOT LAT (ms)"]
TRACKING_KEYS = list(get_args(TRACKING_KEYS_TYPE))

sort_key_handler: dict[TRACKING_KEYS_TYPE, Callable[[tuple[str, LatencyStat]], Union[int,float,str]]] = {
    "FUNCTION": lambda item: item[0],
    "CALLS": lambda item: item[1].invocation,
    "AVG LAT (ms)": lambda item: item[1].avgLatency,
    "MAX LAT (ms)": lambda item: item[1].maxLatency,
    "MIN LAT (ms)": lambda item: item[1].minLatency,
    "TOT LAT (ms)": lambda item: item[1].sumLatency
}

__latencies: dict[str, LatencyStat] = defaultdict(LatencyStat.new)

def __get_function_name(function: Callable[P, R]):
    return function.__qualname__ or function.__name__

@overload
def track(function_or_unit: Callable[P, R]) -> Callable[P, R]:
    """
    Decorator to regiser a function for tracing

    Args:
        function_or_unit (`Callable[P, R]`): Register the function for tracing with default unit config (milliseconds)

    Example usage::
    ```py
    @track
    def hello(seconds: int):
        import time
        time.sleep(seconds)
        return seconds
    ```
    """
    ...

@overload
def track(function_or_unit: UnitInfo) -> Callable[[Callable[P, R]], Callable[P, R]]:
    """
    Decorator to regiser a function for tracing

    Args:
        function_or_unit (`UnitInfo`): Register the function for tracing with desired unit

    Example usage::
    ```py
    @track(UnitInfo(unit='s', converter=1e9))
    def hello2(seconds: int):
        import time
        time.sleep(seconds)
        return seconds
    ```
    """
    ...

def track(function_or_unit: Union[Callable[P, R], UnitInfo]):
    """
    Decorator to regiser a function for tracing

    Args:
        function_or_unit (`Callable[P, R]` | `UnitInfo`): Register the function for tracing with desired units or with default unit config

    Example usage::
    ```py
    @track
    def hello(seconds: int):
        import time
        time.sleep(seconds)
        return seconds
    @track(UnitInfo(unit='s', converter=1e9))
    def hello2(seconds: int):
        import time
        time.sleep(seconds)
        return seconds
    ```
    """
    global __latencies
    def internal_track(_function: Callable[P, R]):
        if isinstance(function_or_unit, UnitInfo):
            __latencies[__get_function_name(_function)].unitMeta = function_or_unit
        def wrapper(*args: P.args, **kwargs: P.kwargs) -> R: # type: ignore
            start_time = time.time_ns()
            total_time = 0
            try:
                out = _function(*args, **kwargs)
                if inspect.isgenerator(out):
                    for item in out:
                        total_time += time.time_ns() - start_time
                        start_time = time.time_ns()
                        yield item # type: ignore
                    return
                else:
                    total_time = time.time_ns() - start_time
                    return out
            except:
                raise
            finally:
                __latencies[__get_function_name(_function)].add_entry(
                    time.time_ns() - start_time if total_time == 0 else total_time
                )
        return wrapper
    if isinstance(function_or_unit, UnitInfo):
        return internal_track
    else:
        return internal_track(function_or_unit)

def print_stats(sort_key: TRACKING_KEYS_TYPE, compact: bool = False, reverse: bool = False, clear: bool = True):
    """
    Print Current tracing stats

    Args:
        sort_key (`TRACKING_KEYS_TYPE`): Key to sort the stats based on
        compact (`bool`): Whether to print in compact mode
        reverse (`bool`): Descending order
        clear (`bool`): Do you want the stats to be cleared ? Make it false if you want a running stat
    """
    global TRACKING_KEYS, __latencies, sort_key_handler

    row_format = "| {:>40} | {:^20} | {:<20.4f} | {:<20.4f} | {:<20.4f} | {:<20.4f} |"
    head_format = row_format.replace(".4f", "")
    empty_format = head_format.replace('|', '_')
    
    if compact:
        row_format = row_format.replace('|', '')
        head_format = head_format.replace('|', '')

    # print(head_format.split(':'))
    empty_items = [int(item[1:3]) for item in head_format.split(':') if '0' in item]
    empty_str = empty_format.format(*['_'*item for item in empty_items])

    lines = 1

    if not compact:
        print(empty_str)
        lines += 1
    print(head_format.format(*TRACKING_KEYS))
    if not compact:
        lines += 1
        print(empty_str)
    
    for function_name, stat in sorted(__latencies.items(), key=sort_key_handler[sort_key], reverse=reverse):
        if stat.invocation == 0:
            continue
        lines += 1
        print(row_format.format(*[
            sort_key_handler[key]((function_name, stat)) if key in ["FUNCTION", "CALLS"] 
            else sort_key_handler[key]((function_name, stat)) / stat.unitMeta.converter # type: ignore
            for key in TRACKING_KEYS
        ]))
    
    if clear and lines > 0:
        print("", end=f'\033[{lines}F')

def get_stats():
    """
    Get Current tracing stats
    """
    global __latencies
    return __latencies
