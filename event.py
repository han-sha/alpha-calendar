from datetime import datetime, timedelta
from sqlalchemy import extract, and_
import re, random

class Event(object):
	def __init__(self, sessID=None, jdID=None, year=None, month=None, day=None,
	 hour=None, minute=None, duration=None, event_type=None, event_detail=None, 
	 nearest=None, isUpdate=False, isDelete=False):

		self.exclusion = ['所有计划', '忽略此项', '事务', '原始']

		self.sessID = sessID
		self.jdID = jdID

		self.duration = duration
		self.event_type = event_type
		if isDelete is False:
			self.event_detail = event_detail if event_detail not in self.exclusion else None
		else:
			self.event_detail = event_detail

		self.year = year
		self.month = month
		self.day = day
		self.hour = hour
		self.minute = minute

		self.end_datetime = None
		self.start_datetime = None

		self.isUpdate = isUpdate
		self.weekday = {}

		if day is not None:
			self.__get_datetime()
			self.__get_weekday()

	def __get_datetime(self):
		if self.isUpdate is True and self.hour is None:
			return

		hour = self.hour if self.hour is not None else 0
		minute = self.minute if self.minute is not None else 0

		self.start_datetime = datetime(self.year, self.month, 
			self.day, hour, minute, 0)

		if self.duration is not None:
			self.__calc_endtime()


	def __calc_endtime(self):
		if type(self.duration).__name__ == 'timedelta':
			self.end_datetime = self.start_datetime + self.duration
		elif self.duration is not None:
			dur_week = re.findall(r'(\d+)W', self.duration)
			dur_day = re.findall(r'(\d+)D', self.duration)
			dur_hour = re.findall(r'(\d+)H', self.duration)
			dur_min = re.findall(r'(\d+)M', self.duration)

			if (not dur_week) and (not dur_day) and (not dur_hour) and (not dur_min):
				self.end_datetime = self.start_datetime
			else:
				dur_week = 0 if not dur_week else int(dur_week[0])
				dur_day = 0 if not dur_day else int(dur_day[0]) + (dur_week*7)
				dur_hour = 0 if not dur_hour else int(dur_hour[0])
				dur_min = 0 if not dur_min else int(dur_min[0])
				self.duration = timedelta(days=dur_day, hours=dur_hour, minutes=dur_min)
				self.end_datetime = self.start_datetime + self.duration


	def __get_weekday(self):
		f = open('weekday', 'r')
		lines = f.readlines()
		for l in lines:
			l = l.rstrip().split(' ')
			self.weekday[int(l[0])] = l[1]

	def get_diff_between_now_start(self):
		now = datetime.now()
		rst = self.start_datetime - now
		return rst

	def get_diff_between_now_end(self):
		now = datetime.now()
		rst = self.end_datetime - now
		return rst


	def time_des_gen(self, start=True):
		_hour = self.start_datetime.hour if start is True else self.end_datetime.hour
		_minute = self.start_datetime.minute if start is True else self.end_datetime.minute

		if _hour is None and _minute is None:
			return ''

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

		if _minute is not None:
			hour_ending = "点" if _minute == 0 else "点" + str(_minute) + "分"
		else:
			hour_ending = ''

		return phrase + str(_hour) + hour_ending


	def day_des_gen(self, start=True):
		now = datetime.now()

		_year = self.year if start is True else self.end_datetime.year
		_month = self.month if start is True else self.end_datetime.month
		_day = self.day if start is True else self.end_datetime.day

		year_diff = _year - now.year
		month_diff = _month - now.month
		day_diff = _day - now.day

		day = ''

		# weekday calculation
		_now = datetime(now.year, now.month, now.day)
		_start = datetime(_year, _month, _day)

		_diff = _start - _now
		_diff = _diff.days
		if 2 < _diff <= (6 - _now.weekday()):
			return '这个' + self.weekday[_start.weekday()]
		elif 6 < _diff <= (13 - _now.weekday()):
			return '下个' + self.weekday[_start.weekday()]

		if year_diff == 0:
			year = ''
		elif year_diff == 1:
			year = '明年'
		else:
			year = str(_year) + '年'

		if (year_diff == 0) & (month_diff == 0) & (day_diff > 2) & start is True:
			month = '这个月'
		elif (year_diff == 0) & (month_diff == 0) & (day_diff <= 2):
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
		elif (year_diff == 0) & (month_diff == 0) & (day_diff == -1):
			day = '昨天'
		elif (year_diff == 0) & (month_diff == 0) & (day_diff == -2):
			day = '前天'
		else:
			day = str(_day) + '号'

		return year + month + day


	def duration_des_gen(self):
		diffDay = self.duration.days
		diffSeconds = self.duration.seconds

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


	def __get_tense(self):
		if self.is_future() is True:
			tense_verb = "将持续"
			yuji_verb = '预计'
			tense_guo = ''
		else:
			tense_verb = "已经花费了"
			yuji_verb = ''
			tense_guo = '过'

		return tense_verb, tense_guo, yuji_verb


	def get_des(self, anstype=None):
		duration = self.duration_des_gen()
		tense_verb, tense_guo, yuji_verb = self.__get_tense()
		phrase = ''

		if anstype == '有什么事要做':
			phrase += self.time_des_gen(start=True)
			phrase += '您有' + tense_guo + '一条为时' + duration + '的' + self.event_detail + '计划。'

		else:
			phrase += self.day_des_gen(start=True) + self.time_des_gen(start=True) + '，'
			phrase += '您有'  + tense_guo + '一条' + self.event_detail +  '计划，'
			if duration != 0:
				phrase += '此计划' + tense_verb  + duration + '，'
				phrase += yuji_verb + '结束时间为' + self.day_des_gen(start=False) + self.time_des_gen(start=False) + '。 '
			else:
				phrase += '只是您并没有记录' + self.event_detail + '要花费多长时间。' 
		return phrase


	def get_year(self):
		if self.year is None:
			return None
		return int(self.year)

	def get_month(self):
		if self.month is None:
			return None
		return int(self.month)

	def get_day(self):
		if self.day is None:
			return None
		return int(self.day)

	def get_hour(self):
		if self.hour is None:
			return None
		return int(self.hour)

	def get_minute(self):
		if self.minute is None:
			return None
		return int(self.minute)

	def get_startime(self):
		if self.start_datetime is None:
			return None
		return self.start_datetime

	def get_endtime(self):
		if self.end_datetime is None:
			return None
		return self.end_datetime

	def get_duration(self):
		if self.duration is None:
			return None
		return self.duration

	def get_sessID(self):
		return self.sessID

	def get_detail(self):
		return self.event_detail


	def is_future(self):
		diff = self.get_diff_between_now_start()
		days = diff.days
		seconds = diff.seconds
		micro = diff.microseconds

		if days < 0 or seconds < 0 or micro < 0:
			return False
		else:
			return True

	def change(self, startyear=None, startmonth=None, startday=None, starthour=None, 
		startminute=None, endyear=None, endmonth=None, endday=None, endhour=None,
		endminute=None, detail=None, duration=None):
		print(self.year)
		if duration is not None:
			self.duration = duration
		if startyear is not None:
			self.year = startyear
		if startmonth is not None:
			self.month = startmonth
		if startday is not None:
			self.day = startday
		if starthour is not None:
			self.hour = starthour
		if startminute is not None:
			self.minute = startminute
		print(self.duration)
		self.__get_datetime()
		self.__get_weekday()