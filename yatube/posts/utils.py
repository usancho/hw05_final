from django.core.paginator import Paginator

CONST_CUT = 10


def paginate(paginate_var, request):
    paginator = Paginator(paginate_var, CONST_CUT)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    return {'page_obj': page_obj, }
