from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import get_list_or_404, get_object_or_404, render
from django.urls import reverse

from .models import Department, Employee

#####


# Create your views here.


def index(request):
    """Основная страница приложения по адресу /emp/
    Здесь надо сделать таблицу - перечень отделов
    """
    departments = Department.objects.all()
    context = {"departments": departments}

    TEMP = "emp/departments.html"

    rc = render(request, TEMP, context)

    return rc


def emp_index(request, number):
    """Страница списка сотрудников отдела"""
    department = get_object_or_404(Department, number=number)
    employees = Employee.objects.filter(department__exact=department)
    context = {"employees": employees, "department": department}
    return render(request, "emp/emplist.html", context)


def emp_view(request, tablenumber):
    """Форма - редактор сотрудника"""
    employee = Employee.objects.get(tablenumber__exact=tablenumber)
    department = Department.objects.get(number__exact=employee.department.number)
    context = {"employee": employee, "department": department}
    return render(request, "emp/empview.html", context)


def emp_store(request, tablenumber):
    """Процедура сохранения данных сотрудника"""
    employee = Employee.objects.get(tablenumber__exact=tablenumber)
    employee.personname = request.POST["personname"]
    employee.save()
    return HttpResponseRedirect(reverse("dep_index"))
    # return HttpResponseRedirect(reverse("emp_view"), args=(tablenumber,))
