from datetime import datetime
from event import Event
from agenda import Agenda
from sqlalchemy import extract, and_
import random


class Add(object):
	def __init__(self, db, jdID, timestamps, event):

		self.exclusion = ['所有计划', '忽略此项', '事务', '原始', None]

		self.db = db
		self.jdID = jdID
		self.e = event
		self.timestamps = timestamps

		self.year = event.get_year()
		self.month = event.get_month()
		self.day = event.get_day()
		self.detail = event.get_detail()
		self.duration = event.get_duration()
		self.details = []

		self.__pop_details()

	def __pop_details(self):
		f = open('detail', 'r')
		lines = f.readlines()
		for l in lines:
			l = l.rstrip()
			self.details.append(l)


	def __which_add(self):
		diff = self.e.get_diff_between_now_start()
		if (diff.days < 0) or (diff.seconds < 0) or (diff.microseconds < 0):
			rst = self.__pastevent_error_gen()
			return rst
		if self.detail not in self.details:
			rst = '抱歉，暂不支持您所添加的计划类型，请您参考技能说明上所支持的类型进行添加。类型在不断扩展，期待您的宝贵意见。'
			return rst
		if self.duration is None:
			rst = self.__duration_error_gen()
			return rst
		rst = self.__add()
		return rst

	def __duration_error_gen(self):
		return '请您告诉我该计划预计几点结束，或者需要多久噢。您可以说，我要添加' + self.e.day_des_gen() + self.e.time_des_gen()\
		+ '到某某时刻的' + self.detail + '，或者我要添加' + self.e.day_des_gen() + self.e.time_des_gen() + '开始预计需要几个小时的'\
		+ self.detail + '。'


	def __pastevent_error_gen(self):
		error = ["您的行程本只能协助您规划未来的计划，并不支持记录以往的事务哈。", 
		"出错了哦，您要添加的计划已经是过去时了。", "出错了哦，过去的计划您也加，我都傻傻分不清楚了。"]
		num = random.randrange(0, len(error), 1)
		return error[num]


	def __add(self):
		agenda = Agenda(timestamps=self.timestamps, sessID=self.e.get_sessID(), jdID=self.jdID, 
			agendaType=self.detail, startTime=self.e.get_startime(), 
			endTime=self.e.get_endtime(), agendaDetail=self.detail)

		try:
			self.db.session.add(agenda)
			self.db.session.commit()
		except Exception as err:
			self.__log_error(err)
			rst = "您的规划本出了点小问题，这条计划添加失败了..."
			return rst

		rst = "已成功帮您添加了" + self.e.day_des_gen() + self.e.time_des_gen() + '开始，预计在' + self.e.day_des_gen(start=False)\
		+ self.e.time_des_gen(start=False) + '结束的' + self.detail + '计划哈。'

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