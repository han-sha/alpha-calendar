from datetime import datetime

class QueriedEvent(object):
	def __init__(self, e):
		self.startYear = e[0].year
		self.startMonth = e[0].month
		self.startDay = e[0].day
		self.startHour = e[0].hour
		self.startMinute = e[0].minute

		self.endYear = e[1].year
		self.endMonth = e[1].month
		self.endDay = e[1].day
		self.endHour = e[1].hour
		self.endMinute = e[1].minute

		self.duration = e[1] - e[0]

		self.startDatetime = e[0]
		self.endDatetime = e[1]
		self.type = e[2]
		self.detail = e[3]


	def __time_des_gen(self, start=True):
		hour = self.startHour if start is True else self.endHour
		minute = self.startMinute if start is True else self.endMinute

		if hour < 12:
			phrase = "早上"
		elif hour == 12 and minute == 0:
			phrase = "中午"
		elif 12 < hour < 18:
			hour = hour - 12
			phrase = "下午"
		else:
			hour = hour - 12
			phrase = "晚上"

		if minute == 0:
			hour_ending = "点"
		else:
			hour_ending = "点" + str(minute) + "分"

		return phrase + str(hour) + hour_ending

	def __duration_des_gen(self):
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

	def __day_des_gen(self, start=True):
		now = datetime.now()

		_year = self.startYear if start is True else self.endYear
		_month = self.startMonth if start is True else self.endMonth
		_day = self.startDay if start is True else self.endDay

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
		duration = self.__duration_des_gen()
		tense_verb, tense_guo, yuji_verb = self.__get_tense()
		phrase = ''

		if anstype == '有什么事要做':
			phrase += self.__time_des_gen(start=True)
			phrase += '您有' + tense_guo + '一条为时' + duration + '的' + self.detail + '计划。'

		else:
			phrase += self.__day_des_gen(start=True) + self.__time_des_gen(start=True) + '，'
			phrase += '您有'  + tense_guo + '一条关于' + self.detail +  '的计划，'
			if duration != 0:
				phrase += '此计划' + tense_verb  + duration + '，'
				phrase += yuji_verb + '结束时间为' + self.__day_des_gen(start=False) + self.__time_des_gen(start=False) + '。 '
			else:
				phrase += '只是您并没有记录' + self.detail + '要花费多长时间。' 
		return phrase


	def get_startYear(self):
		return self.startYear

	def get_startMonth(self):
		return self.startMonth

	def get_startDay(self):
		return self.startDay

	def get_startHour(self):
		return self.startHour

	def get_startMinute(self):
		return self.startMinute

	def get_endYear(self):
		return self.endYear

	def get_endMonth(self):
		return self.endMonth

	def get_endDay(self):
		return self.endDay

	def get_endHour(self):
		return self.endHour

	def get_endMinute(self):
		return self.endMinute

	def get_duration(self):
		return self.duration

	def get_startDatetime(self):
		return self.startDatetime

	def get_endDatetime(self):
		return self.endDatetime

	def get_type(self):
		return self.type

	def get_detail(self):
		return self.detail

	def between_now_start(self):
		now = datetime.now()
		rst = self.startDatetime - now
		return rst

	def between_now_end(self):
		now = datetime.now()
		rst = self.endDatetime - now
		return rst


	def is_future(self):
		diff = self.between_now_start()
		days = diff.days
		seconds = diff.seconds

		if days < 0 or seconds < 0:
			return False
		else:
			return True