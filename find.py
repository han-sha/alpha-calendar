from datetime import datetime
from getevent import GetEvent
from queriedevent import QueriedEvent
from agenda import Agenda
from sqlalchemy import extract, and_
import random

class Find(object):
	def __init__(self, db, jdID, event, nearest=False, anstype=None):
		self.db = db
		self.jdID = jdID
		self.e = event
		self.nearest = nearest

	def find(self):
		rst = self.__which_find()
		return rst


	def __which_find(self):
		date = self.e.get_date()
		time = self.e.get_time()
		detail = self.e.get_detail()
		nearest = self.nearest

		if date is None and time is None and detail is None:
			rst = self.__find_none()
		elif time is None and detail is None:
			rst = self.__find_all()
		elif date is None and time is None and nearest is True:
			rst = self.__find_next()
		elif detail is None:
			rst = self.__find_event(date=date)
		else:
			rst = self.__confirm(date=date)

		return rst



	def __find_next(self):
		detail = self.e.get_detail()
		event = self.db.session.query(
			Agenda.startTime, Agenda.endTime, Agenda.agendaDetail).filter(and_(
				Agenda.jdID==self.jdID,
				Agenda.agendaDetail == detail)).first()
		if len(event) == 0:
			rst = '您还没有安排下次的' + detail + '哟。您可以回复添加计划来规划下一次的' + detail + '。'
		else:
			year, month, day, hour, minute = event[0].year, event[0].month, \
			event[0].day, event[0].hour, event[0].minute
			startime, endtime = event[0], event[1]

			rst = '您下一次的' + detail + '是在' + self.__day_des_gen(year=year, month=month, day=day) + \
			self.__time_des_gen(hour=hour, minute=minute) + ',' + \
			'预计需要' + self.__duration_des_gen(start=startime, end=endtime)
		return rst



	def __find_event(self, date=None):
		now = datetime.now()
		year, month, day = now.year, now.month, now.day if date is None \
		else self.e.get_year(), self.e.get_month(), self.e.get_day()

		hour, minute = self.e.get_hour(), self.e.get_minute()

		events = self.db.session.query(
			Agenda.startTime, Agenda.endTime, Agenda.agendaDetail).filter(and_(
				Agenda.jdID==self.jdID, 
				extract('year', Agenda.startTime) == year,
				extract('month', Agenda.startTime) == month,
				extract('day', Agenda.startTime) == day,
				extract('hour', Agenda.startTime) == hour,
				extract('minute', Agenda.startTime == minute))).all()
		minute = '' if minute == 0 else str(minute) + '分'
		if len(events) == 0:
			pos = '今天' + str(hour) + '点，' if date is None else \
			self.__day_des_gen() + self.__time_des_gen()
			rst = '您还没有在' + pos + '安排任何计划哟。您可以回复添加来增加新计划。'

		else:
			for e in events:
				event = QueriedEvent(e)
				rst += event.get_des(anstype=anstype)

		return rst


	def __find_none(self):
		phrase = ['''不是很确定您想查什么噢，给我一点线索吧。
		比如您可以这样问：查一下我今天都有什么安排。或者，查查我今天是不是要去开会等等。''', 
		'''请问您具体想查点什么呢？比如您可以说：我想查今天几点开会。或者您也可以问：
		查查我今天9点是不是要去开会。''']
		n = random.randrange(0, len(phrase), 1)
		return phrase[n]


	def __find_all(self, anstype=None):
		diff = self.e.get_diff_between_now_start()
		if diff.days > 7:
			rst = "不好意思哈，您的规划本只保存过去一星期内的记录。超过一星期的已经被自动删除了哟"
			return rst 

		year = self.e.get_year()
		month = self.e.get_month()
		day = self.e.get_day()

		events = self.db.session.query(
			Agenda.startTime, Agenda.endTime, Agenda.agendaType, Agenda.agendaDetail).filter(and_(
				Agenda.jdID==self.jdID, 
				extract('year', Agenda.startTime) == year,
				extract('month', Agenda.startTime) == month,
				extract('day', Agenda.startTime) == day)).all()

		if len(events) == 0:
			rst = "您的行程本还没有记录这天的任何计划哈"
			return rst
		else:
			n = len(events)
			if (diff.days < 0) or (diff.seconds < 0):
				rst = "这天的" if anstype == '有什么事要做' \
				else "在过去的这天里，您规划了" + str(n) + "条事项："
			else:
				rst = "这天的" if anstype == '有什么事要做' \
				else "在未来的这天里，您规划了" + str(n) + "条事项："
			for e in events:
				event = QueriedEvent(e)
				rst += event.get_des(anstype=anstype)
		return rst


	def __time_des_gen(self, hour=None, minute=None):
		_hour = self.e.get_hour() if hour is None else hour
		_minute = self.e.get_minute() if minute is None else minute

		if _hour < 12:
			phrase = "早上"
		elif _hour == 12 and _minute == 0:
			phrase = "中午"
		elif 12 < _hour < 18:
			_hour = _hour - 12
			phrase = "下午"
		else:
			_hour = _hour - 12
			phrase = "晚上"

		if _minute == 0:
			hour_ending = "点"
		else:
			hour_ending = "点" + str(_minute) + "分"

		return phrase + str(_hour) + hour_ending


	def __day_des_gen(self, year=None, month=None, day=None, start=True):
		now = datetime.now()

		_year = self.e.get_year() if year is None else year
		_month = self.e.get_month() if month is None else month
		_day = self.e.get_day() if day is None else day

		year_diff = _year - now.year
		month_diff = _month - now.month
		day_diff = _day - now.day

		day = ''

		if year_diff == 0:
			year = ''
		elif year_diff == 1:
			year = '明年'
		else:
			year = str(_year) + '年'

		if (year_diff == 0) & (month_diff == 0) & (day_diff > 2) & start is True:
			month = '这个月'
		elif (year_diff == 0) & (month_diff == 0) & (day_diff < 2):
			month = ''
		elif (year_diff == 0) & (month_diff == 1):
			month = '下个月'
		else:
			month = str(_month) + '月'

		if (year_diff ==0) & (month_diff == 0) & (day_diff == 0):
			day = '今天'
		elif (year_diff == 0) & (month_diff == 0) & (day_diff == 1):
			day = '明天'
		elif (year_diff == 0) & (month_diff == 0) & (day_diff == 2):
			day = '后天'
		else:
			day = str(_day) + '号'

		return year + month + day


	def __duration_des_gen(self, start, end):
		duration = end - start
		diffDay = duration.days
		diffSeconds = duration.seconds

		year = 0
		month = 0
		phrase = ''
		if diffDay >= 365:
			year = diffDay/365
			diffDay = diffDay%365
			phrase = str(int(year)) + '年'
		if diffDay >= 30:
			month = diffDay/30
			diffDay = diffDay%30
			phrase += str(int(month)) + '月'
		if diffDay >= 1:
			phrase += str(int(diffDay)) + '天'
		if year >= 1 or month >= 1 or diffDay >= 1:
			return phrase + '左右'

		if diffSeconds>= 3600:
			hour = diffSeconds/3600
			diffSeconds = diffSeconds%3600
			phrase = str(int(hour)) + '小时'
		if diffSeconds >= 60:
			minute = diffSeconds/60
			phrase += str(int(minute)) + '分钟'

		return phrase