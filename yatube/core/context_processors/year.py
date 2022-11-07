from datetime import date


def year(request):
    """Добавляет текущий год"""
    return {'year': date.today().year, }
