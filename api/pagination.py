
from rest_framework.pagination import PageNumberPagination

class ProductPagination(PageNumberPagination):
    page_size = 10  # Default items per page
    page_size_query_param = 'page_size'  # Allow user to override page size
    max_page_size = 100

class UserOrdersPagination(PageNumberPagination):
    page_size = 3  # Default items per page
    page_size_query_param = 'page_size'  # Allow user to override page size
    max_page_size = 100