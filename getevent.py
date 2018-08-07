from datetime import datetime, timedelta
from agenda import Agenda
from queriedevent import QueriedEvent
from sqlalchemy import extract, and_
import re, random

class GetEvent(object):
	def __init__(self, db=None, sessID=None, jdID=None, date=None, time=None, duration=None, 
		event_type=None, event_detail=None, isAdd=False):

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

		self.isAdd = isAdd

		self.exclusion = ['所有计划', '忽略此项', '事务', '原始']

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

		if self.isAdd is True:
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
		if (self.event_detail in self.exclusion):
			rst = '您计划的具体内容有点奇怪，添加失败了。'
			return rst

		agenda = Agenda(sessID=self.sessID, jdID=self.jdID, 
			agendaType=self.event_type, startTime=self.start_datetime, 
			endTime=self.end_datetime, agendaDetail=self.event_detail)

		try:
			self.db.session.add(agenda)
			self.db.session.commit()
		except Exception as err:
			self.__log_error(err)
			rst = "您的规划本出了点小问题，这条计划添加失败了..."
			return rst

		rst = "已成功帮您添加了这条计划，感谢您的使用哈"
		return rst


	def find_events(self, anstype=None):
		if self.time is None:
			events = self.db.session.query(
			Agenda.startTime, Agenda.endTime, Agenda.agendaType, Agenda.agendaDetail).filter(and_(
				Agenda.jdID==self.jdID, 
				extract('year', Agenda.startTime) == self.year,
				extract('month', Agenda.startTime) == self.month,
				extract('day', Agenda.startTime) == self.day)).all()

		if len(events) == 0:
			rst = "您的行程本还没有记录这天的任何计划哈"
			return rst

		else:
			n = len(events)
			diff = self.get_diff_between_now_start()
		if (diff.days < 0) or (diff.seconds < 0):
			rst = "这天的" \
			 if anstype == '有什么事要做' else "在过去的这天里，您规划了" + str(n) + "条事项："
		else:
			rst = "这天的"\
			if anstype == '有什么事要做' else "在未来的这天里，您规划了" + str(n) + "条事项："
		for e in events:
			event = QueriedEvent(e)
			rst += event.get_des(anstype=anstype)
		return rst


	def delete_events(self):
		record = []
		if self.event_detail == '所有计划':
			events = self.db.session.query(Agenda).filter(and_(Agenda.jdID==self.jdID, 
				extract('year', Agenda.startTime) == self.year, extract('month', Agenda.startTime) == self.month, 
				extract('day', Agenda.startTime) == self.day)).all()
		elif self.time == None:
			events = self.db.session.query(Agenda).filter(and_( Agenda.jdID==self.jdID, extract('year', Agenda.startTime) == self.year, 
				extract('month', Agenda.startTime) == self.month, extract('day', Agenda.startTime) == self.day, 
				Agenda.agendaDetail == self.event_detail)).all()
		else:
			events = self.db.session.query(Agenda).filter(and_(Agenda.jdID==self.jdID, extract('year', Agenda.startTime) == self.year,
				extract('month', Agenda.startTime) == self.month,extract('day', Agenda.startTime) == self.day, 
				extract('hour', Agenda.startTime) == self.hour,  
				extract('minute', Agenda.startTime) == self.minute)).all()
		if not events:
			rst = '没有找到您需要删除的这条计划，请回复查找或添加来查询或添加这条计划'
			return rst

		try:
			for item in events:
				self.db.session.delete(item)
				record.append(item)
			self.db.session.commit()

		except Exception as err:
			self.__log_error(err)
			rst = "抱歉...您的规划本出了点小问题，计划删除失败了..."
			return rst

		rst = '已经帮您删除这' + str(len(record)) + '条计划：'
		for e in record:
			minute = '' if e.startminute() == 0 else str(e.startminute()) + '分'
			rst += str(e.startyear()) + '年' + str(e.startmonth()) + '月' + str(e.startday()) + '号' + str(e.starthour()) + '点' + minute +'的' + e.detail() + '计划，'

		rst += '感谢您的使用！'
		return rst


	def get_year(self):
		return int(self.year)

	def get_month(self):
		return int(self.month)

	def get_day(self):
		return int(self.day)

	def get_hour(self):
		return int(self.hour)

	def get_startime(self):
		return self.start_datetime

	def get_duration(self):
		return self.duration


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
