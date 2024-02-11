import pytest
from application.common.pagination import Pagination, PaginatedApi


class TestPagination:
    def test_paginate(self):
        # Create a mock query object
        class MockQuery:
            def __init__(self, count):
                self._count = count

            def count(self):
                return self._count

            def limit(self, per_page):
                return self

            def offset(self, offset):
                return self

            def all(self):
                return []

        query = MockQuery(count=100)
        page = 1
        per_page = 10

        pagination = Pagination.paginate(query, page, per_page, unused=False)

        assert pagination.total == 100
        assert pagination.pages == 10
        assert pagination.has_prev == False
        assert pagination.has_next == True
