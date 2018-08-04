
class Event(object):
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