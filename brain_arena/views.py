from django.shortcuts import render


def custom_404(request, exception):
    """Кастомная страница ошибки 404."""
    return render(request, 'errors/404.html', status=404)