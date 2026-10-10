import hmac
import json

from django.conf import settings
from django.core.paginator import Paginator
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, render
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST

from .models import Course
from .services import process_webhook


def course_list(request):
    page = Paginator(Course.objects.filter(is_visible=True), 12).get_page(request.GET.get("page"))
    return render(request, "hotmart/course_list.html", {"page_obj": page, "selected_category": "cursos"})


def course_detail(request, slug):
    course = get_object_or_404(Course, slug=slug, is_visible=True)
    return render(request, "hotmart/course_detail.html", {"course": course, "selected_category": "cursos"})


@require_POST
@csrf_exempt
def hotmart_webhook(request):
    if not settings.HOTMART_HOTTOK:
        return HttpResponse(status=503)
    if not hmac.compare_digest(request.headers.get("X-HOTMART-HOTTOK", "").encode(), settings.HOTMART_HOTTOK.encode()):
        return HttpResponse(status=403)
    try:
        payload = json.loads(request.body)
        if not isinstance(payload, dict):
            raise ValueError
        process_webhook(payload)
    except (ValueError, UnicodeDecodeError):
        return HttpResponse(status=400)
    return HttpResponse(status=200)
