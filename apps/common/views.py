from django.http import HttpResponseRedirect
from django.shortcuts import render
from django.contrib.admin.views.decorators import staff_member_required
from rest_framework.views import exception_handler
from rest_framework.response import Response


def custom_exception_handler(exc, context):
    response = exception_handler(exc, context)
    if response is not None:
        errors = response.data
        if isinstance(errors, dict):
            for field, msgs in errors.items():
                if isinstance(msgs, list):
                    errors[field] = [str(m) for m in msgs]
                else:
                    errors[field] = str(msgs)
        response.data = {
            'error': True,
            'detail': errors,
        }
    return response


def root_redirect(request):
    return HttpResponseRedirect('/cms/login/')


@staff_member_required
def dashboard(request):
    return render(request, 'admin/dashboard.html')
