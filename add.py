from datetime import datetime
from event import Event
from agenda import Agenda
from sqlalchemy import extract, and_
import random


class Add(object):
	def __init__(self, db, jdID, event):

		self.exclusion = ['所有计划', '忽略此项', '事务', '原始']

		self.db = db
		self.jdID = jdID
		self.e = event

		self.year = event.get_year()
		self.month = event.get_month()
		self.day = event.get_day()


	def __which_add(self):
		diff = self.e.get_diff_between_now_start()
		if (diff.days < 0) or (diff.seconds < 0) or (diff.microseconds < 0):
			rst = self.__pastevent_error_gen()
			return rst
		if (self.e.get_detail() in self.exclusion):
			rst = '您计划的具体内容有点奇怪，添加失败了。'
			return rst
		rst = self.__add()
		return rst


	def __pastevent_error_gen(self):
		error = ["您的行程本只能协助您规划未来的计划，并不支持记录以往的事务哈", 
		"出错了哦，您要添加的计划已经是过去时了", "出错了哦，过去的计划您也加，我都傻傻分不清楚了"]
		num = random.randrange(0, len(error), 1)
		return error[num]


	def __add(self):
		agenda = Agenda(sessID=self.e.get_sessID(), jdID=self.jdID, 
			agendaType=self.e.get_detail(), startTime=self.e.get_startime(), 
			endTime=self.e.get_endtime(), agendaDetail=self.e.get_detail())

		try:
			self.db.session.add(agenda)
			self.db.session.commit()
		except Exception as err:
			self.__log_error(err)
			rst = "您的规划本出了点小问题，这条计划添加失败了..."
			return rst

		rst = "已成功帮您添加了这条计划，感谢您的使用哈"
		return rst


	def __log_error(self, err):
		f = open('err/add.err', 'a')
		f.write(str(err))
		f.write('\n')
		f.write('\n')
		f.close()


	def add(self):
		rst = self.__which_add()
		return rst