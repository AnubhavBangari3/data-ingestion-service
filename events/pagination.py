from rest_framework.pagination import PageNumberPagination


class EventPagination(PageNumberPagination):
    # Default number of records returned per page
    page_size = 20
    # Allows clients to override page size using ?page_size=
    page_size_query_param = "page_size"
    # Maximum page size allowed to prevent very large responses
    max_page_size = 100