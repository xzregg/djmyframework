import calendar
import datetime
import math

import arrow

TIMEZONE = 'Asia/Shanghai'

DATETIME_FORMAT = 'YYYY-MM-DD HH:mm:ss'
NORMAL_DATE_FORMAT = 'YYYY-MM-DD'
FULL_DATETIME_FORMAT = 'YYYY-MM-DD HH:mm:ss:SSSS,X'


def get_date_between(start_date, end_date, is_abs=True):
    """
    获取两个日期之间相隔多少天
    """

    date_delta = end_date - start_date
    date_between = int(math.fabs(date_delta.days) if is_abs else date_delta.days)
    return date_between


def get_weeks_between(start_date, end_date):
    """
    获取两个日期之间相隔多少天
    datetime 类型加上 .date 获取日期
    """
    week_start = start_date - datetime.timedelta(days=start_date.weekday())
    week_end = end_date - datetime.timedelta(days=end_date.weekday())
    return (week_end - week_start).days // 7


def compare_two_date(first, last, fmt='YYYY-MM-DD'):
    """
    两个时间比较

    first_date < last_date : < 0
    first_date > last_date : > 0
    first_date = last_date : = 0
    """
    first_date = arrow.get(first)
    last_date = arrow.get(last)

    if first_date > last_date:
        return 1
    elif first_date < last_date:
        return -1
    else:
        return 0


def get_date_by_fmt(*args, **kwargs):
    return arrow.get(*args, **kwargs).replace(tzinfo=TIMEZONE)


def get_date(date=None):
    return arrow.get(date or get_now()).replace(tzinfo=TIMEZONE)


def get_date_start_end(date):
    day_start_end = date.span('day')
    day_start = day_start_end[0]
    day_end = day_start_end[1]
    return day_start, day_end


def whether_date_in_date_between(start, end, date):
    """
    某个日期是否在某两个确切的日期区间内
    """
    _start = get_date(start)
    _end = get_date(end)
    _date = get_date(date)

    if not _start <= _end:
        raise AttributeError('start_date must smaller than end_date')

    return _start <= _date <= _end


def get_current_hours(hour=+0, fmt='YYYY-MM-DD HH:mm:ss'):
    """
    获取当前时间并根据hour做调整
    :param fmt:
    :param hour:
    :return:
    """
    return arrow.now().replace(hours=hour).format(fmt=fmt)


def format_date(date, fmt=DATETIME_FORMAT) -> object:
    """
    格式化时间
    :param date:  'YYYY-MM-DD' or datetime or '2018-12-19T09:29:00' else
    :param fmt:
    :return:
    """
    return get_date(date).format(fmt=fmt)


def get_now():
    """
    获取当前时间
    :return:  arrow
    """
    return arrow.now()


def replace_day(date, days=+0, fmt='YYYY-MM-DD'):
    """
    获取当前时间并根据days做调整, 默认为当天
    days: +1, -1
    """
    if not date:
        date = arrow.now()
    return get_date(date).replace(days=days).format(fmt)


def time_to_datetime(hour, minute, second):
    """将time类型转datetime"""
    return datetime.datetime.now().replace(hour=hour, minute=minute, second=second)


def get_date_floor(date, frame='day', is_format=False):
    """
    获取时间的底
    :param date:
    :param frame: day/hour
    :return:
    """
    return format_date(get_date(date).floor(frame)) if is_format else get_date(date).floor(frame)


def get_date_ceil(date, frame='day', is_format=False):
    """
    获取时间的顶
    :param date:
    :param frame: day/hour
    :return:
    """
    return format_date(get_date(date).ceil(frame)) if is_format else get_date(date).ceil(frame)


def shift_month_date(months=-0, fmt='YYYY-MM-DD'):
    """
    偏移时间-按月来偏移
    :return:
    """
    return get_date().shift(months=months).format(fmt)


def date_to_datetime(date: datetime.date):
    """
    时间日期转 开始时间00:00 结束日期23:59:59
    :return:
    """
    start_time = f"{date} 00:00:00"
    end_time = f"{date} 23:59:59"
    return start_time, end_time


def sec_to_str(param):
    """
    秒转为时分秒字符串
    """
    m, s = divmod(param, 60)
    h, m = divmod(m, 60)
    if h >= 24:
        h -= 24
    return "%02d:%02d:%02d" % (h, m, s)


def str_to_sec(param):
    """
    字符串时分秒转换成秒
    """
    h, m, s = param.strip().split(':')
    return int(h) * 3600 + int(m) * 60 + int(s)


def time_to_sec(y):
    """
    时间类型时分秒转换成秒
    """
    h = y.hour  # 直接用datetime.time模块内置的方法，得到时、分、秒
    m = y.minute
    s = y.second
    return int(h) * 3600 + int(m) * 60 + int(s)  # int()函数转换成整数运算


def sec_to_time(seconds):
    seconds = int(seconds)
    m, s = divmod(seconds, 60)
    h, m = divmod(m, 60)
    return f"%02d:%02d:%02d" % (h, m, s)


def get_current_timestamp():
    return str(get_now().timestamp)


def get_now_weekday():
    """
    用于外卖的 weekday
    """
    weekday = get_now().weekday()
    if 4 <= get_now().hour < 10:  # 4:00 - 9:59
        hour = 0
    elif 10 <= get_now().hour < 15:  # 10:00 - 14:59
        hour = 1
    elif 15 <= get_now().hour < 20:  # 15:00 - 20:00
        hour = 2
    else:  # 20:00 - 3:59
        hour = 3
    return 1 << (weekday * 4 + hour)


def get_date_remain(start_date, end_date):
    """
    获取剩余剩余的时间

    eg:
        start_date = '2019-03-03',  end_date = '2020-02-02' return (336, 0, 0, 0)
        start_date = '2020-03-25 05:33:23',  end_date = '2020-03-26 12:40:13' return (1, 7, 6, 50)
        start_date = '2020-03-26 05:33:23',  end_date = '2020-03-26 12:40:13' return (0, 7, 6, 50)
    """
    start = get_date(start_date)
    end = get_date(end_date)
    delta = end - start

    days = delta.days  # 剩余天数
    hours, remainder = divmod(delta.seconds, 3600)  # 剩余小时数
    minutes, seconds = divmod(remainder, 60)  # 获取剩余小时

    return days, hours, minutes, seconds


def get_datetime(date, fmt='%Y-%m-%d %H:%M:%S'):
    return datetime.datetime.strptime(date, fmt)


def get_date_range(date, frame='day'):
    """
    返回当日时间低和定的时间范围,用于orm range条件
    :param date:
    :return:
    """
    return (format_date(get_date_floor(date, frame)), format_date(get_date_ceil(date, frame)))


def get_every_day(begin_date, end_date):
    """
    获得两个日期中所有有效日期
    """
    date_list = []
    # begin_date = datetime.datetime.strptime(begin_date, "%Y-%m-%d")
    # end_date = datetime.datetime.strptime(end_date, "%Y-%m-%d")
    while begin_date <= end_date:
        date_str = begin_date.strftime("%Y-%m-%d")
        date_list.append(date_str)
        begin_date += datetime.timedelta(days=1)
    return date_list


def get_time_between(start_time, end_time, time=None):
    """判断现在是否在这两个时间内"""
    now = get_now()
    start_date = now.format('YYYY-MM-DD')

    if end_time < start_time:
        end_date = now.shift(days=1).format('YYYY-MM-DD')
    else:
        end_date = now.format('YYYY-MM-DD')

    start_time = datetime.datetime.strptime(start_date + ' ' + str(start_time), '%Y-%m-%d %H:%M:%S')
    end_time = datetime.datetime.strptime(end_date + ' ' + str(end_time), '%Y-%m-%d %H:%M:%S')
    now_time = datetime.datetime.now() if not time else time
    if end_time > now_time > start_time:
        return True
    return False


def get_current_week():
    """获得今天星期几"""
    return datetime.datetime.today().isoweekday()


# def get_week(y, w):
#     """
#     根据周号获取那周的所有日期
#     用法：get_week(2023,26)
#     返回：[datetime.date(2023, 6, 26),
#  datetime.date(2023, 6, 27),
#  datetime.date(2023, 6, 28),
#  datetime.date(2023, 6, 29),
#  datetime.date(2023, 6, 30),
#  datetime.date(2023, 7, 1),
#  datetime.date(2023, 7, 2)]
#
#     """
#     first = next(
#             (datetime.date(y, 1, 1) + datetime.timedelta(days=i)
#              for i in range(367)
#              if (datetime.date(y, 1, 1) + datetime.timedelta(days=i)).isocalendar()[1] == w and
#                 (datetime.date(y, 1, 1) + datetime.timedelta(days=i)).isocalendar()[0] == y
#              ))
#     return [first + datetime.timedelta(days=i) for i in range(7)]


def get_week(y, w):
    """
    根据周号获取那周的所有日期
    用法：get_week(2023, 26)
    返回：[datetime.date(2023, 6, 26),
           datetime.date(2023, 6, 27),
           datetime.date(2023, 6, 28),
           datetime.date(2023, 6, 29),
           datetime.date(2023, 6, 30),
           datetime.date(2023, 7, 1),
           datetime.date(2023, 7, 2)]
    """
    # 检查周号是否在合理范围内
    start_date = datetime.date(y, 1, 1)
    if start_date.weekday() > 3:
        start_date += datetime.timedelta(7 - start_date.weekday())
    else:
        start_date -= datetime.timedelta(start_date.weekday())
    delta = datetime.timedelta(days=(w - 1) * 7)
    start_of_week = start_date + delta
    return [start_of_week + datetime.timedelta(days=i) for i in range(7)]


def get_current_date():
    """获得今天日期"""
    return datetime.datetime.now().strftime('%Y-%m-%d')


def calculate_age(birth):
    """计算年龄，少于1岁用日差除以365计算"""
    birth_d = birth
    today_d = datetime.datetime.now().date()
    if today_d.month > birth_d.month:
        age = today_d.year - birth_d.year
    elif today_d.month == birth_d.month:
        if today_d.day >= birth_d.day:
            age = today_d.year - birth_d.year
        else:
            age = today_d.year - birth_d.year - 1
    else:
        age = today_d.year - birth_d.year - 1

    if age <= 0:
        date_between = get_date_between(birth_d, today_d)
        age = round(date_between / 365, 2)
    return age


def get_month_last_day():
    """获取每月最后日期"""
    today = datetime.datetime.now()
    return calendar.monthrange(today.year, today.month)[1]


def get_today_sec():
    """获取今天进行秒数"""
    now = datetime.datetime.now()
    return now.hour * 60 * 60 + now.minute * 60 + now.second


def get_week_start_and_end():
    today = datetime.datetime.now().date()
    start_date = today - datetime.timedelta(today.weekday())
    end_date = today + datetime.timedelta(7 - today.weekday() - 1)
    return start_date, end_date


def get_month_start_and_end(time=None):
    """
    返回当月第一天和最后一天时间范围,用于orm range条件
    :param date:
    :return: ('YYYY-MM-01 00:00:00', 'YYYY-MM-DD 23:59:59')
    """
    if not time:
        time = datetime.datetime.now()
    last_day = calendar.monthrange(time.year, time.month)[1]
    start_date = get_datetime(get_date_range(time.replace(day=1))[0])
    end_date = get_datetime(get_date_range(time.replace(day=last_day))[1])
    return start_date, end_date


def is_leap_year(years):
    if (years % 4 == 0 and years % 100 != 0) or (years % 400 == 0):  # 判断是否是闰年
        days_sum = 366
        return days_sum
    else:
        days_sum = 365
        return days_sum


def get_this_year_after_day():
    # 获取今天开始后到今年结束的日期
    start_date = datetime.datetime.now().date()
    start_date_str = start_date.strftime("%Y-%m-%d")
    years = start_date_str[0:4]

    end_date = datetime.datetime.strptime(f"{years}-12-31", "%Y-%m-%d").date()

    all_date_list = []
    while start_date < end_date:
        # b = arrow.get(start_date).shift(days=next_day_num).format("YYYY-MM-DD")
        start_date_str = start_date.strftime("%Y-%m-%d")
        all_date_list.append(start_date_str)
        start_date += datetime.timedelta(days=1)

    return all_date_list


def judge_weekday(time_date, is_saturday=False, is_sunday=False):
    # 0:周一 1:周二 2:周三 3:周四 4:周五 5:周六 6:周日
    today = datetime.datetime.strptime(time_date, "%Y-%m-%d")
    if is_saturday:
        return True if int(today.weekday()) == 5 else False
    elif is_sunday:
        return True if int(today.weekday()) == 6 else False
    else:
        return True if int(today.weekday()) == 5 or int(today.weekday()) == 6 else False


def judge_weekend_days(date_list):
    saturday_days = []
    sunday_days = []
    all_weekend_days = []
    for i in date_list:
        if judge_weekday(i, is_saturday=True):
            saturday_days.append(i)
        if judge_weekday(i, is_sunday=True):
            sunday_days.append(i)
        if judge_weekday(i):
            all_weekend_days.append(i)

    return saturday_days, sunday_days, all_weekend_days


def get_month_all_date_str(today=None):
    import pandas as pd
    # 获取本月的所有日期，没有传today是拿系统时间的本月所有日期
    all_date_str_list = []
    now = datetime.datetime.now()
    if today:
        now = today
    this_month_end = datetime.datetime(now.year, now.month, calendar.monthrange(now.year, now.month)[1]).strftime("%Y-%m-%d")
    this_month_start = datetime.datetime(now.year, now.month, 1)

    all_date = pd.date_range(this_month_start, this_month_end)
    for date in all_date:
        date_str = date.strftime("%Y-%m-%d")
        all_date_str_list.append(date_str)
    return all_date_str_list


def get_month_range(year, month):
    """返回这个月的第一天和最后一天"""
    start_date = datetime.date(year, month, 1)
    next_month = start_date.replace(day=28) + datetime.timedelta(days=4)  # 获取下个月的前一天
    end_date = next_month - datetime.timedelta(days=next_month.day)
    return start_date, end_date


def get_lastweek_day(weekday, date=None):
    """
    获取上周日期
    @param weekday: 上周星期几 0 周一， 4 为周五
    @return:
    """

    today = date or datetime.date.today()

    pred = today + datetime.timedelta(days=-7)
    pred += datetime.timedelta(days=weekday - pred.weekday())
    return pred


def number_convert_to_weekly_date(number):
    """
    0-> 本周周一日期
    1-> 本周周二日期
    2-> 本周周三日期
    。。。
    6-> 本周周日日期

    """
    today = datetime.date.today()
    days_ahead = number - today.weekday()
    target_date = today + datetime.timedelta(days=days_ahead)
    return target_date


def nature_week(date):
    """自然周（周日至周六）的数据"""
    weekday = date.weekday()
    if weekday == 6:
        start_date = date
        end_date = date + datetime.timedelta(6)
    else:
        start_date = date - datetime.timedelta(weekday + 1)
        end_date = date + datetime.timedelta(7 - date.weekday() - 2)
    return start_date, end_date


def calculate_age_by_id_number(id_number):
    """根据身份证号码获取年龄，按年份算"""
    age = None
    try:
        if len(id_number) == 18:
            birth_year = int(id_number[6:10])
            birth_month = int(id_number[10:12])
            birth_day = int(id_number[12:14])
        else:
            birth_year = int('19' + id_number[6:8])
            birth_month = int(id_number[8:10])
            birth_day = int(id_number[10:12])
        today = datetime.date.today()
        age = today.year - birth_year
        # if (today.month, today.day) < (birth_month, birth_day):
        #     age -= 1
    except:
        pass
    return age
