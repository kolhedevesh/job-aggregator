import math


def test_pagination_calculation():
    total = 30
    page_size = 10
    total_pages = math.ceil(total / page_size)
    assert total_pages == 3

    total = 25
    total_pages = math.ceil(total / page_size)
    assert total_pages == 3


def test_pagination_slicing():
    items = list(range(30))
    page_size = 10
    # page 1
    start = (1 - 1) * page_size
    end = start + page_size
    assert items[start:end] == list(range(0, 10))
    # page 3
    start = (3 - 1) * page_size
    end = start + page_size
    assert items[start:end] == list(range(20, 30))
