import math


def test_pagination_calculation():
    total = 30
    page_size = 10
    total_pages = math.ceil(total / page_size)
    assert total_pages == 3

    total = 25
    total_pages = math.ceil(total / page_size)
    assert total_pages == 3
