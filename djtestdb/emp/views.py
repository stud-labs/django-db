from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import get_list_or_404, get_object_or_404, render
from django.urls import reverse
from django.core.exceptions import ValidationError
from django.db.utils import InternalError

from .models import Department, Employee

from django.db import connection
from django.contrib import messages
from recordclass import recordclass
import inspect

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
            try:
                cursor.execute('call "UPDATE_EMPLOYEE"(%s,%s,%s,%s,%s);',vls)
                cursor.execute('commit;')
                messages.success(request,"The employee has been updated!")
            except InternalError as e:
                msg = str(e).split("CONTEXT")[0]
                messages.error(request, msg)
        else:
            try:
                depmo = request.POST["depno"]
                vls[4] = -1
                cursor.execute('call "INSERT_EMPLOYEE"(%s,%s,%s,%s,%s,%s);',vls+[depmo])
                cursor.execute('commit;')
                messages.success(request,"The employee has been added!")
            except InternalError as e:
                msg = str(e).split("CONTEXT")[0]
                messages.error(request, msg)

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
            try:
                cursor.execute('call "DELETE_EMPLOYEE"(%s);', (tablenumber,))
                cursor.execute('commit;')
                messages.success(request,"The employee has been deleted!")
                return HttpResponseRedirect(reverse("dep_index"))
            except InternalError as e:
                msg = str(e).split("CONTEXT")[0]
                messages.error(request, msg)


def namedtuplefetchall(cursor, fields = [], f=None):
    """
    Return all rows from a cursor as a namedtuple.
    Assume the column names are unique.
    """
    desc = cursor.description
    nt_result = recordclass("Result", [col[0] for col in desc] + fields)
    vs = [None] * len(fields)
    def _(row):
        ntr = nt_result(*list(row)+vs)
        if callable(f):
            return f(ntr)
        else:
            return ntr
    return [_(row) for row in cursor.fetchall()]



def dep_rep(request, depno):
    """Report 1 generator for a departement or departments.
    If depno == 0 generate for all the departments
    """
    filter = False
    department = None
    try:
        department = Department.objects.get(number__exact=depno)
        filter = True
    except ValidationError:
        depno="285242ac-fa97-4ccb-b56f-000000000000"
        pass

    with connection.cursor() as cursor:
        cursor.execute('SELECT * from "COUNT_EMP_IN_DEPS"(%s,%s)', (filter,depno))
        def iid(x):
            return x

        def f(r):
            global pd

        result = namedtuplefetchall(cursor, ["last"], iid)
        if result:
            pd = result[0].department
            ll = len(result)-1
            for i,r in enumerate(result):
                r.last=False
                if pd != r.department:
                    result[i-1].last = True
                    pd = r.department
                if i==ll:
                    r.last = True
        context = {"result":result, "department":department}
        return render(request, "emp/deprep.html", context)
