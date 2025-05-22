from rest_framework.pagination import PageNumberPagination


class PageLimitPagination(PageNumberPagination):
    """Кастомный класс пагинации с параметрами page и limit"""
    page_size = 6
    page_size_query_param = 'limit'
    max_page_size = 100
    page_query_param = 'page'
