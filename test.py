from grace import track, get_stats, print_stats, UnitInfo
from time import sleep
# from typing import Callable, Any
import random

@track
def test1():
    d = random.randint(0, 2)
    sleep(d)
    return d

@track(UnitInfo(unit='s', converter=1e9))
def test2():
    d = random.randint(0, 5)
    sleep(d)
    return d

@track(UnitInfo(unit='ms', converter=1e6))
def test3():
    d = random.randint(0, 5)
    sleep(d)
    return d

class Test4:

    @track
    def call1(self):
        d = random.randint(0, 5)
        sleep(d)
        return d
    
    @staticmethod
    @track
    def test1():
        d = random.randint(0, 5)
        sleep(d)
        return d
    
    @track
    def yielder(self):
        for item in (Test4.test1, self.call1, test2):
            yield item()

if __name__ == "__main__":
    t4 = Test4()
    tasks = (
        test1,
        test2,
        test3,
        t4.call1,
        Test4.test1,
        t4.yielder,
        test1,
        test2,
        test3,
        t4.call1,
        Test4.test1,
        t4.yielder
    )
    # random.shuffle(tasks)
    # print([func.__qualname__ or func.__name__ for func in tasks])
    # exit()
    for task in tasks:
        out = task()
        if not isinstance(out, int):
            for item in out:
                print_stats(sort_key="AVG LAT (ms)", clear=True)
                sleep(1)
                print_stats(sort_key="AVG LAT (ms)", clear=True)
        print_stats(sort_key="AVG LAT (ms)", clear=True)
    print_stats(sort_key="AVG LAT (ms)", clear=False)
    print(get_stats())