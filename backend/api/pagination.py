from rest_framework.pagination import PageNumberPagination


class PaginationWithLimit(PageNumberPagination):

    def get_page_size(self, request):
        return request.query_params.get('limit', 6)
