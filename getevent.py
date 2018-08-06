from datetime import datetime
from datetime import timedelta
from agenda import Agenda
from sqlalchemy import extract, and_
import re, random

class GetEvent(object):
	def __init__(self, db, sessID=None, jdID=None, date=None, time=None, duration=None, 
		event_type=None, event_detail=None, isFind=False):

		self.db = db

		self.sessID = sessID
		self.jdID = jdID

		self.date = date
		self.time = time
		self.duration = duration
		self.event_type = event_type
		self.event_detail = event_detail

		self.year = None
		self.month = None
		self.day = None
		self.hour = None
		self.minute = None

		self.end_datetime = None
		self.start_datetime = None

		self.isFind = isFind

		self.__get_datetime()

	def __get_datetime(self):
		date = self.date.split('-')
		self.year = int(date[0])
		self.month = int(date[1])
		self.day = int(date[2])

		if self.time is not None:
			time = self.time.split(':')
			self.hour = int(time[0])
			self.minute = int(time[1])
		else:
			self.hour, self.minute = 0, 0

		self.start_datetime = datetime(self.year, self.month, 
			self.day, self.hour, self.minute, 0)

		if self.isFind is False:
			self.__calc_endtime()


	def __calc_endtime(self):
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


	def __log_error(self, err):
		f = open('err', 'a')
		f.write(str(err))
		f.write('\n')
		f.write('\n')
		f.close()

	def get_diff_between_now_start(self):
		now = datetime.now()
		rst = self.start_datetime - now
		return rst

	def get_diff_between_now_end(self):
		now = datetime.now()
		rst = self.end_datetime - now
		return rst

	def get_add_pastevent_error(self):
		error = ["您的行程本只能协助您规划未来的计划，并不支持记录以往的事务哈", 
		"出错了哦，您要添加的计划已经是过去时了", "出错了哦，过去的计划您也加，我都傻傻分不清楚了"]
		num = random.randrange(0, len(error), 1)
		return error[num]


	def add_event(self):
		agenda = Agenda(sessID=self.sessID, jdID=self.jdID, 
			agendaType=self.event_type, startTime=self.start_datetime, 
			endTime=self.end_datetime, agendaDetail=self.event_detail)

		try:
			self.db.session.add(agenda)
			self.db.session.commit()
		except Exception as err:
			self.__log_error(err)
			rst = "您的行程本出了点小问题，这条行程添加失败了..."
			return rst

		rst = "已成功帮您添加了这条计划，感谢您的使用哈"
		return rst


	def find_events(self):
		if self.time is None:
			events = self.db.session.query(
			Agenda.startTime, Agenda.endTime, Agenda.agendaType, Agenda.agendaDetail).filter(and_(
				Agenda.jdID==self.jdID, 
				extract('year', Agenda.startTime) == self.year,
				extract('month', Agenda.startTime) == self.month,
				extract('day', Agenda.startTime) == self.day)).all()

		return events


	def is_future(self):
		diff = self.between_now_start()
		days = diff.days
		seconds = diff.seconds

		if days < 0 or seconds < 0:
			return False
		else:
			return True