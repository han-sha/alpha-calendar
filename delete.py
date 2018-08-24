from datetime import datetime
from event import Event
from agenda import Agenda
from sqlalchemy import extract, and_
import random


class Delete(object):
	def __init__(self, db, jdID, event, selftime, cmd):
		self.db = db
		self.jdID = jdID
		self.e = event
		self.cmd = cmd

		self.year = event.get_year()
		self.month = event.get_month()
		self.day = event.get_day()

		self.hour = event.get_hour()
		self.minute = event.get_minute()
		self.detail = event.get_detail()
		self.selftime = selftime

		self.details = []
		self.delall_list = ['所有计划', '所有']
		self.froms = ['从', '在']

		self.__pop_details()


	def __pop_details(self):
		f = open('detail', 'r')
		lines = f.readlines()
		for l in lines:
			l = l.rstrip()
			self.details.append(l)


	def __get_ts(self):
		if self.selftime == '上午':
			t1 = datetime(self.year, self.month, self.day, 0, 0)
			t2 = datetime(self.year, self.month, self.day, 11, 59)
		elif self.selftime == '下午':
			t1 = datetime(self.year, self.month, self.day, 12, 0)
			t2 = datetime(self.year, self.month, self.day, 17, 59)
		else:
			t1 = datetime(self.year, self.month, self.day, 18, 0)
			t2 = datetime(self.year, self.month, self.day, 23, 59)
		return t1, t2


	def __sanity_check(self):
		rst = ''
		if self.hour is None and self.year is None and self.cmd is None and self.detail is None:
			rst = '''如果您要清空规划本里的所有计划，您可以说清空所有计划。您也可以指定删除某一类计划，某一时段或某一时刻的计划，
			如：删除今天的所有计划，删除今天的所有会议计划，删除今天早上的所有会议计划，删除今天早上10点的会议计划等。'''
			return False, rst
		return True, rst


	def __which_delete(self):
		check, rst = self.__sanity_check()
		if check is False:
			return rst
		if self.cmd in self.delall_list:
			rst = self.__delete_all()
		elif self.cmd == '最近一次':
			rst = self.__delete_next()
		elif self.selftime is not None:
			rst = self.__delete_timedomain()
		else:
			rst = self.__delete_one()
		return rst


	def __delete_one(self):
		des = ''
		events = self.db.session.query(Agenda).filter(and_(Agenda.jdID==self.jdID, 
				extract('year', Agenda.startTime) == self.year, extract('month', Agenda.startTime) == self.month, 
				extract('day', Agenda.startTime) == self.day,
				extract('hour', Agenda.startTime) == self.hour,
				extract('minute', Agenda.startTime) == self.minute)).all()
		rst, des = '', ''
		for e in events:
			a = e.make_event()
			des += a.day_des_gen() + a.time_des_gen() + '的' + a.get_detail() + '。'
			if e.detail() == self.detail:
				try:
					self.db.session.delete(e)
					self.db.session.commit()
				except Exception as err:
					self.__log_error(err)
					rst = "抱歉...您的规划本出了点小问题，计划删除失败了..."
					return rst
				rst = '已成功帮您删除' + self.e.day_des_gen() + self.e.time_des_gen() + \
				'的' + self.detail + '计划 。'
		return rst


	def __delete_next(self):
		record = None
		query = self.db.session.query(Agenda).filter(and_(Agenda.jdID==self.jdID, 
				Agenda.agendaDetail == self.detail))
		event = query.order_by(Agenda.startTime).first()
		if not event:
			rst = '您还没有规划关于' + self.detail + '的计划呢。您可以回复我要添加计划，来进行添加噢！'
			return rst
			
		record = event.make_event()
		try:
			self.db.session.delete(event)
			self.db.session.commit()

		except Exception as err:
			self.__log_error(err)
			rst = "抱歉...您的规划本出了点小问题，计划删除失败了..."
			return rst

		rst = '您下次的' + self.detail + '是在' + record.day_des_gen() + record.time_des_gen() + \
		'，已经成功帮您删除啦。'
		return rst


	def __delete_all_all(self):
		record = []
		events = self.db.session.query(Agenda).filter(and_(Agenda.jdID==self.jdID)).all()
		if len(events) == 0:
			rst = '您的规划本里什么计划都还没有噢。您可以回复添加计划来进行添加。'
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

		rst = '已经帮您删除' + str(len(record)) + '条计划了哟。您的规划本现已被清空。'
		return rst



	def __delete_all_details(self):
		record = []
		des = ''
		events = self.db.session.query(Agenda).filter(and_(Agenda.jdID==self.jdID,
			Agenda.agendaDetail == self.detail)).all()
		if len(events) == 0:
			rst = '您的规划本里还没有任何关于' + self.detail + '的计划噢。您可以回复添加计划来进行添加。'
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

		for n, e in enumerate(record):
			a = e.make_event()
			des += a.day_des_gen() + a.time_des_gen() if n+1 == len(record) else a.day_des_gen() + a.time_des_gen() + '，'

		rst = '已经帮您删除' + str(len(record)) + '条计划了哟。'
		return rst



	def __more_than_one(self, events):
		rst = '在' + self.e.day_des_gen() + self.selftime + '您有' + str(len(events)) + '条' + self.detail + '的计划，它们分别将'
		tmp = events[0].make_event()
		for n, e in enumerate(events):
			n = random.randrange(0, 2, 1)
			e = e.make_event()
			if n == len(events)-1:
				rst += '以及' + self.froms[n] + e.time_des_gen() + '开始，' + e.time_des_gen(False) + '结束。'
			else:
				rst += self.froms[n] + e.time_des_gen() + '开始，' + e.time_des_gen(False) + '结束；'
		rst += '请问您要删除哪一条呢？比如您可以说，我要删除' + tmp.day_des_gen() + tmp.time_des_gen() + '的' + tmp.get_detail() + '计划。'
		rst += '如果您想将这' + str(len(events)) + '条计划全部删除，您也可以说，删除' + tmp.day_des_gen() + self.selftime 
		rst += '的所有'
		rst += '' if self.detail is None else self.detail
		rst += '计划。'
		return rst



	def __delete_one(self, e):
		try:
			self.db.session.delete(e)
			record.append(e)
			self.db.session.commit()

		except Exception as err:
			self.__log_error(err)
			rst = "抱歉...您的规划本出了点小问题，计划删除失败了..."
			return rst

		e = e.make_event()
		rst = '已经帮您删除了' + e.day_des_gen() + self.selftime + '的' + self.detail + '计划。'
		rst += '该计划的原定时间是' + e.day_des_gen() + e.time_des_gen() + '，原预定在' + e.day_des_gen(False) + e.time_des_gen(False)
		rst += '结束。'
		return rst



	def __delete_timedomain(self):
		record = []
		t1, t2 = self.__get_ts()
		if self.detail is None:
			events = self.db.session.query(Agenda).filter(and_(Agenda.jdID==self.jdID, 
				extract('year', Agenda.startTime) == self.year, extract('month', Agenda.startTime) == self.month, 
				extract('day', Agenda.startTime) == self.day,
				Agenda.startTime.between(t1, t2))).all()
			if len(events) == 0:
				rst = '您还没有在' + self.e.day_des_gen() + self.selftime + '添加如何计划噢，请先进行添加。'
			elif len(events) > 1:
				rst = self.__more_than_one(events)
			else:
				rst = self.__delete_one(events[0])

		else:
			events = self.db.session.query(Agenda).filter(and_(Agenda.jdID==self.jdID, 
					extract('year', Agenda.startTime) == self.year, extract('month', Agenda.startTime) == self.month, 
					extract('day', Agenda.startTime) == self.day,
					Agenda.startTime.between(t1, t2),
					Agenda.agendaDetail==self.detail)).all()
			if len(events) == 0:
				rst = '您还没有在'+ self.e.day_des_gen() + self.selftime + '制定任何有关' + self.detail + '的计划呢，您可以先进行添加哈。'
				return rst
			elif len(events) > 0:
				rst = self.__more_than_one(events)
			else:
				rst = self.__delete_one(events[0])
		return rst



	def __delete_all_selftime_details():
		record = []
		t1, t2 = self.__get_ts()
		events = self.db.session.query(Agenda).filter(and_(Agenda.jdID==self.jdID, 
				extract('year', Agenda.startTime) == self.year, extract('month', Agenda.startTime) == self.month, 
				extract('day', Agenda.startTime) == self.day,
				Agenda.startTime.between(t1, t2),
				AgendaDetail=self.detail)).all()
		if len(events) == 0:
			rst = '您还没有在'+ self.e.day_des_gen() + self.selftime + '制定任何有关' + self.detail + '的计划呢，您可以先进行添加哈。'
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

		rst = '已经帮您删除' + str(len(record)) + '条计划了哟。这些计划是：'
		for e in record:
			a = e.make_event()
			rst += a.day_des_gen() + a.time_des_gen() + a.get_detail() + '计划。'
		return rst



	def __delete_all(self):
		if self.detail is None and self.year is None:
			rst = self.__delete_all_all()
		elif self.year is not None:
			rst = self.__delete_day()
		elif self.detail is not None:
			rst = self.__delete_all_details()
		else:
			rst = self.__delete_all_selftime_details()
		return rst


	def __delete_day(self):
		if self.selftime is None:
			rst = self.__delete_day_all()
		else:
			rst = self.__delete_day_selftime_all()
		return rst



	def __delete_day_details(self):
		record = []
		events = self.db.session.query(Agenda).filter(and_(Agenda.jdID==self.jdID, 
			extract('year', Agenda.startTime) == self.year, extract('month', Agenda.startTime) == self.month, 
			extract('day', Agenda.startTime) == self.day,
			Agenda.agendaDetail == self.detail)).all()
		if len(events) == 0:
			rst = '您还没有制定'+ self.e.day_des_gen() + '的' + self.e.get_detail() + '计划呢，您可以先进行添加哈。'
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

		rst = '已经帮您删除' + str(len(record)) + '条计划了哟。这些计划是：'
		for e in record:
			a = e.make_event()
			rst += a.day_des_gen() + a.time_des_gen() + a.get_detail() + '计划。'
		return rst


	def __delete_day_all(self):
		record = []
		events = self.db.session.query(Agenda).filter(and_(Agenda.jdID==self.jdID, 
				extract('year', Agenda.startTime) == self.year, extract('month', Agenda.startTime) == self.month, 
				extract('day', Agenda.startTime) == self.day)).all()
		if len(events) == 0:
			rst = '您还没有在'+ self.e.day_des_gen() + '制定任何计划呢，您可以先进行添加哈。'
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

		rst = '已经帮您删除' + str(len(record)) + '条计划了哟。这些计划是：'
		for e in record:
			a = e.make_event()
			rst += a.day_des_gen() + a.time_des_gen() + a.get_detail() + '计划。'
		return rst



	def __delete_day_selftime_all(self):
		record = []
		t1, t2 = self.__get_ts()
		events = self.db.session.query(Agenda).filter(and_(Agenda.jdID==self.jdID, 
				extract('year', Agenda.startTime) == self.year, extract('month', Agenda.startTime) == self.month, 
				extract('day', Agenda.startTime) == self.day,
				Agenda.startTime.between(t1, t2))).all()
		if len(events) == 0:
			rst = '您还没有在'+ self.e.day_des_gen() + self.selftime + '制定任何计划呢，您可以先进行添加哈。'
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

		rst = '已经帮您删除' + str(len(record)) + '条计划了哟。这些计划是：'
		for e in record:
			a = e.make_event()
			rst += a.day_des_gen() + a.time_des_gen() + a.get_detail() + '计划。'
		return rst


	def __log_error(self, err):
		f = open('err/delete.err', 'a')
		f.write(str(err))
		f.write('\n')
		f.write('\n')
		f.close()


	def delete(self):
		rst = self.__which_delete()
		return rst

