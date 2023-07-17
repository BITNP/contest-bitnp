from django.shortcuts import render

config_origin = {
    'year':'2023',      # 年
    'month':'9',        # 月

    # 试题相关
    'score':'100',      # 总分
    'cnt':'10',         # 题目数
    'time_limit':'150', # 限时（秒）
    'change':'2',       # 答题次数
}

def index_config(request):
    config = {
        'year':config_origin['year'],
        'month':config_origin['month'],
        'cnt':config_origin['cnt'],
        'time_limit':config_origin['time_limit'],
        'change':config_origin['change'],
    }
    return render(request, 'index.html', {'config':config})

def info_config(request):
    config = {
        'year':config_origin['year'],
        'month':config_origin['month'],
        'score':config_origin['score'],
        'change':config_origin['change'],
    }
    return render(request, 'info.html', {'config':config})