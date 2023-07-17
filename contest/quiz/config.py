from django.shortcuts import render

def index_config(request):
    config = {
        'year':'2023',      # 年
        'month':'9',        # 月
        'cnt':'10',         # 题目数
        'time_limit':'150', # 限时（秒）
        'change':'2',       # 答题次数
    }
    return render(request, 'index.html', {"config":config})

def base_config(request):
    config = {
        'year':'2023',
    }
    return render(request, 'base.html', {'config':config})