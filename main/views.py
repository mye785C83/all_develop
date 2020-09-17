from django.shortcuts import render, redirect, get_object_or_404
from .forms import *
from .models import *
from accounts.models import User
import datetime, calendar


def index(request):
    return render(request, 'base.html')


def mapping_cal(user, year, month, mode):
    cal = calendar.month(year, month)
    cal = cal.split('\n')

    data = {
        'title': cal[0],
        'year': year,
        'month': month,
    }

    # 스케줄 관리
    if mode == 1:
        weeks = loading_all_plans(year, month, cal)
    # 조회
    elif mode == 2:
        results = loading_individual_logs(user, year, month, cal)
        weeks = results[0]
        data['all_hours'] = results[1]
    # 출근 예정
    else:
        weeks = loading_weekly(user, year, month, cal)
        data['weeks'] = weeks
        return data

    weeks.pop()

    if len(weeks[0]) != 7:
        print(type(weeks[0]))
        while len(weeks[0]) < 7:
            weeks[0].insert(0, " ")

    data['weeks'] = weeks

    print(data)
    return data


def loading_individual_logs(user, year, month, cal):
    all_hours = 0
    weeks = []
    for i in range(2, len(cal)):
        line = cal[i]
        dates = line.split()
        days = []
        for day in dates:
            today = datetime.datetime(year=year, month=month, day=int(day))
            logs = Log.objects.filter(date=today, user=user)
            if logs:
                day = {'date': int(day), 'log': logs[0]}
                all_hours += logs[0].hours
            else:
                day = {'date': int(day)}
            days.append(day)

        weeks.append(days)

    return (weeks, all_hours)


def loading_all_plans(year, month, cal):
    weeks = []
    for i in range(2, len(cal)):
        line = cal[i]
        dates = line.split()
        days = []
        for day in dates:
            today = datetime.datetime(year=year, month=month, day=int(day))
            plans = Plan.objects.filter(date=today)
            if plans:
                people = len(plans)
                plan_all = []
                for plan in plans:
                    individual_plan = {
                        'username': str(plan.user.username),
                        'start': plan.start,
                        'end': plan.end
                    }
                    plan_all.append(individual_plan)
                    #한 명의 plan이 dict 형태로 그 dict를 list로 묶음
                day = {'date': int(day), 'plans': plan_all, 'people': people}
            else:
                day = {'date': int(day)}
            days.append(day)

        weeks.append(days)

    return weeks


def loading_weekly(user, year, month, cal):
    weeks = []
    index = 0
    for i in range(2, len(cal)):
        if i == len(cal) - 1:
            break
        line = cal[i]
        dates = line.split()
        week = {}
        days = []
        for day in dates:
            today = datetime.datetime(year=year, month=month, day=int(day))
            if Plan.objects.filter(date=today, user=user):
                plan = Plan.objects.get(date=today, user=user)
                day = {'date': int(day), 'form': plan}
            else:
                day = {'date': int(day)}
            days.append(day)

        week['days'] = days
        week['index'] = index
        index += 1
        if i == len(cal) - 2:
            week['type'] = 'last'
        elif i == 2:
            week['type'] = 'first'
        else:
            week['type'] = '-'
        weeks.append(week)


    if len(weeks[0]['days']) != 7:
        print(type(weeks[0]['days']))
        while len(weeks[0]['days']) < 7:
            weeks[0]['days'].insert(0, " ")

    return weeks


def plan(request):
    user = request.user
    today = datetime.datetime.now()
    data = mapping_cal(user, today.year, today.month, 0)
    print(data)
    if request.method == "POST":
        form = request.POST
        year = int(form['year'])
        month = int(form['month'])
        move = form['move']
        if move == "before":
            if month == 1:
                move_datetime = datetime.datetime(year=year - 1, month=12, day=1)
            else:
                move_datetime = datetime.datetime(year=year, month=month - 1, day=1)
            data = mapping_cal(user, move_datetime.year, move_datetime.month, 0)
        else:
            if month == 12:
                move_datetime = datetime.datetime(year=year + 1, month=1, day=1)
            else:
                move_datetime = datetime.datetime(year=year, month=month + 1, day=1)

            data = mapping_cal(user, move_datetime.year, move_datetime.month, 0)
    return render(request, 'plan.html', data)


def schedule_inquiry(request):
    user = request.user
    today = datetime.datetime.now()
    data = mapping_cal(user, today.year, today.month, 1)
    if request.method == "POST":
        form = request.POST
        year = int(form['year'])
        month = int(form['month'])
        move = form['move']
        if move == "before":
            if month == 1:
                move_datetime = datetime.datetime(year=year - 1, month=12, day=1)
            else:
                move_datetime = datetime.datetime(year=year, month=month - 1, day=1)
            data = mapping_cal(user, move_datetime.year, move_datetime.month, 1)
        else:
            if month == 12:
                move_datetime = datetime.datetime(year=year + 1, month=1, day=1)
            else:
                move_datetime = datetime.datetime(year=year, month=month + 1, day=1)

            data = mapping_cal(user, move_datetime.year, move_datetime.month, 1)
    return render(request, 'schedule_inquiry.html', data)


def input(request):
    if request.method == "POST":
        form = CreateLog(request.POST)
        if form.is_valid():
            log = form.save(commit=False)
            log.user = User.objects.get(username=request.user)
            log.save()
            print(request.user)
            return redirect('look_up')
    else:
        form = CreateLog()
    return render(request, 'input.html', {'form': form})


def input_edit(request):
    if request.method == "POST":
        pk = int(request.POST['pk'])
        log = Log.objects.get(pk=pk)
        print(log)
        form = CreateLog(instance=log)
        print(form)
        return render(request, 'input_edit.html', {'form': form, 'pk': pk })


def save_input(request, pk):
    log = Log.objects.get(pk=pk)
    if request.method == "POST":
        form = CreateLog(request.POST, instance=log)
        if form.is_valid():
            log = form.save(commit=False)
            log.user = User.objects.get(username=request.user)
            log.save()
            print(request.user)
            return redirect('look_up')
        return redirect('input_edit')


def look_up(request):
    user = request.user
    today = datetime.datetime.now()
    data = mapping_cal(user, today.year, today.month, 2)
    if request.method == "POST":
        form = request.POST
        year = int(form['year'])
        month = int(form['month'])
        move = form['move']
        if move == "before":
            if month == 1:
                move_datetime = datetime.datetime(year=year-1, month=12, day=1)
            else:
                move_datetime = datetime.datetime(year=year, month=month-1, day=1)
            data = mapping_cal(user, move_datetime.year, move_datetime.month, 2)
        else:
            if month == 12:
                move_datetime = datetime.datetime(year=year+1, month=1, day=1)
            else:
                move_datetime = datetime.datetime(year=year, month=month+1, day=1)

            data = mapping_cal(user, move_datetime.year, move_datetime.month, 2)

    return render(request, 'look_up.html', data)


def save_plan(request):
    if request.method == "POST":
        print(request.POST)
        result = dict(request.POST)
        values = list(result.values())[2:]
        print(values)
        values_day = []
        value_day = {}
        for i in range(len(values)):
            if i % 3 == 0:
                if i != 0:
                    values_day.append(value_day)
                    value_day = {}
                value_day['date'] = values[i][0]
            elif i % 3 == 1:
                value_day['start'] = values[i][0]
            else:
                value_day['end'] = values[i][0]
        for value in values_day:
            if value['start'] != '' and value['end'] != '':
                user = User.objects.get(username=request.user)
                if Plan.objects.filter(date=value['date'], user=user):
                    plan = Plan.objects.get(date=value['date'], user=user)
                else:
                    plan = Plan()
                    plan.date = value['date']
                    plan.user = user
                plan.start = value['start']
                plan.end = value['end']
                plan.save()

    print("흠")
    print(values_day)

    return redirect('schedule_inquiry')