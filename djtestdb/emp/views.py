from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import get_list_or_404, get_object_or_404, render
from django.urls import reverse

from .models import Department, Employee

from django.db import connection
from django.contrib import messages
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

def emp_new(request, depno):
    """Форма - добавления нового сотрудника"""
    employee = Employee(tablenumber=0)
    department = Department.objects.get(number__exact=depno)
    context = {"employee": employee, "department": department}
    return render(request, "emp/empview.html", context)

def emp_store(request, tablenumber):
    """Процедура сохранения данных сотрудника"""
    flds='personname birthdate email jobposition tablenumber'
    # employee = Employee.objects.get(tablenumber__exact=tablenumber)
    vls = [request.POST[k] for k in flds.split()]
    # employee.personname = request.POST["personname"]
    # employee.save()
    with connection.cursor() as cursor:
        if tablenumber!=0:
            cursor.execute('call "UPDATE_EMPLOYEE"(%s,%s,%s,%s,%s);',vls)
            cursor.execute('commit;')
            messages.success(request,"The employee has been updated!")
        else:
            depmo = request.POST["depno"]
            vls[4] = -1
            cursor.execute('call "INSERT_EMPLOYEE"(%s,%s,%s,%s,%s,%s);',vls+[depmo])
            cursor.execute('commit;')
            messages.success(request,"The employee has been added!")

    return HttpResponseRedirect(reverse("dep_index"))
    # return HttpResponseRedirect(reverse("emp_view"), args=(tablenumber,))


def emp_rm(request, tablenumber, confirm):
    """Форма-запрос на подтверждение удаления сотрудника """
    if confirm!=1:
        employee = Employee.objects.get(tablenumber__exact=tablenumber)
        department = Department.objects.get(number__exact=employee.department.number)
        context = {"employee": employee, "department": department}
        return render(request, "emp/emprm.html", context)
    else:
        with connection.cursor() as cursor:
            cursor.execute('call "DELETE_EMPLOYEE"(%s);', (tablenumber,))
            cursor.execute('commit;')
            messages.success(request,"The employee has been deleted!")
            return HttpResponseRedirect(reverse("dep_index"))
