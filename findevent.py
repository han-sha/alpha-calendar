from datetime import datetime

class FindEvent(object):
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

		self.today = datetime.now()
		self.curYear = self.today.year
		self.curMonth = self.today.month
		self.curDay = self.today.day
		self.curHour = self.today.hour
		self.curMinute = self.today.minute

		self.start = datetime(self.startYear, self.startMonth, self.startDay,
			self.startHour, self.startMinute)
		self.end = datetime(self.endYear, self.endMonth, self.endDay, 
			self.endHour, self.endMinute)

		self.diff_cur_and_start = self.start - self.today
		self.diff_cur_and_end = self.end - self.today
		self.diff_start_and_end = self.end - self.start

		self.eventDetails = e[3]

	def get_time_des(self, start=True):
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

	def get_eventDuration(self):
		diffDay = self.diff_start_and_end.days
		diffSeconds = self.diff_start_and_end.seconds

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

		print(diffSeconds)
		if diffSeconds>= 3600:
			hour = diffSeconds/3600
			diffSeconds = diffSeconds%3600
			phrase = str(int(hour)) + '小时'
		if diffSeconds >= 60:
			minute = diffSeconds/60
			phrase += str(int(minute)) + '分钟'

		return phrase

	# log here needs to be double checked
	def get_day_des(self, start=True):
		diff = self.diff_cur_and_start if start is True else self.diff_cur_and_end

		diff_day = diff.days
		diff_sec = diff.seconds

		year = ''
		month = '这个月'

		if (diff_day > 0) or ((diff_day == 0) and (diff_sec > 0)):
			day = '明天' 
			month = ''
		elif (diff_day < 0) or (diff_sec < 0):
			day = '昨天'
			month = ''
		elif (2 < diff_day < 1) or ((diff_day == 2) and (diff_sec == 0)):
			day = '后天'
			month = ''
		elif (365 < diff_day < 365*2):
			year = '明年' 
			month = ''
		elif (30 < diff_day < 60):
			month = '下个月'
		else:
			day = str(self.startDay) + '号' if start is True else str(self.endDay) + '号'
			month = str(self.startMonth) + '月' if start is True else str(self.endMonth) + '月'
		return year + month + day


	def get_tense(self):
		if (self.startMonth < self.curMonth) or (self.startDay < self.curDay):
			tense_verb = "已经花费了"
			yuji_verb = ''
			tense_guo = '过'
		else:
			tense_verb = "将持续"
			yuji_verb = '预计'
			tense_guo = ''
		return tense_verb, tense_guo, yuji_verb


	def get_overall_des(self):
		duration = self.get_eventDuration()
		tense_verb, tense_guo, yuji_verb = self.get_tense()

		phrase = ''
		phrase += self.get_day_des(start=True) + self.get_time_des(start=True) + '，'
		phrase += '您有'  + tense_guo + '一条关于' + self.eventDetails +  '的计划，'
		if duration != '':
			phrase += '此计划' + tense_verb  + duration + '，'
			phrase += yuji_verb + '结束时间为' + self.get_day_des(start=False) + self.get_time_des(start=False) + '。 '
		else:
			phrase += '只是您并没有记录' + self.eventDetails + '要花费多长时间。' 
		return phrase
