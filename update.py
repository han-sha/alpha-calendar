from event import Event
from agenda import Agenda
from sqlalchemy import extract, and_
from datetime import datetime, timedelta

class Update(object):
	def __init__(self, db, jdID, old_event, new_event, old_selftime, new_selftime):
		self.jdID = jdID
		self.db = db
		self.old_event = old_event
		self.new_event = new_event
		self.details = []
		self.old_selftime = old_selftime
		self.new_selftime = new_selftime

		self.old_detail = self.old_event.get_detail()
		self.new_detail = self.new_event.get_detail()

		self.old_year = self.old_event.get_year()
		self.old_month = self.old_event.get_month()
		self.old_day = self.old_event.get_day()
		self.old_detail = self.old_event.get_detail()
		self.new_year = self.new_event.get_year()
		self.new_month = self.new_event.get_month()
		self.new_day  = self.new_event.get_day()

		self.new_detail = self.old_detail if self.new_detail is None else self.new_detail

		self.__pop_details()

	def __pop_details(self):
		f = open('detail', 'r')
		lines = f.readlines()
		for l in lines:
			l = l.rstrip()
			self.details.append(l)

	def __which_update(self):

		# if self.new_event.is_future() == False:
		# 	rst = "更改失败了，您所给的计划开始时间已过。如需删除计划，请使用删除功能。"
		# 	return rst
		if self.new_detail not in self.details:
			rst = '更改失败了，暂不支持您的新计划类型，请您参考技能说明上所支持的类型进行添加。类型在不断扩展，期待您的宝贵意见。'
			return rst
		if self.old_event.get_hour() is None and self.new_event.get_hour() is None:
			if (self.old_selftime is not None) and (self.new_selftime is not None):
				rst = self.__selftimes()
			elif self.old_selftime is not None:
				rst = self.__old_selftime()
			elif self.new_selftime is not None:
				rst = self.__new_selftime()
			else:
				rst = self.__multiples()
		else:
			rst = self.__singles()

		return rst




	def __get_ts(self):
		year, month, day = self.old_year, self.old_month, self.old_day
		if self.old_selftime == '上午':
			t1 = datetime(year, month, day, 0, 0)
			t2 = datetime(year, month, day, 11, 59)
		elif self.old_selftime == '下午':
			t1 = datetime(year, month, day, 12, 0)
			t2 = datetime(year, month, day, 17, 59)
		else:
			t1 = datetime(year, month, day, 18, 0)
			t2 = datetime(year, month, day, 23, 59)
		return t1, t2



	def __check_ts(self, hour, minute):
		num = int(hour+minute)
		if num < 1159:
			rst = '上午'
		elif num < 1759:
			rst = '下午'
		else:
			rst = '晚上'
		return rst



	def __query_selftime(self, oldtime=True):
		t1, t2 = self.__get_ts()
		check = True
		rst = ''

		query = self.db.session.query(Agenda).filter(and_(Agenda.jdID==self.jdID,
			extract('year', Agenda.startTime) == self.old_year,
			extract('month', Agenda.startTime) == self.old_month,
			extract('day', Agenda.startTime) == self.old_day,
			Agenda.startTime.between(t1, t2),
			Agenda.agendaDetail == self.old_detail))
		event = query.order_by(Agenda.startTime).all()

		if len(event) == 0:
			rst = '对不起，我没有找到' + self.old_event.day_des_gen()
			rst +=  self.old_selftime if oldtime is True else ''
			rst += '有关' + self.old_detail +'的任何计划。请您先用查找功能确定此计划确实存在噢！'
			check = False

		elif len(event) > 1:
			rst = '对不起，您在' + self.old_event.day_des_gen() 
			rst += self.old_selftime if oldtime is True else ''
			rst += '有' + str(len(event)) + '条有关' + self.old_detail +\
			'的计划。分别是'
			for n, a in enumerate(event):
				if n == 0:
					tmp = a.time_des_gen()
				a = a.make_event()
				rst += '从' + a.time_des_gen() + '到' + a.time_des_gen(False) + '，'
			rst += '请您告诉我您要更改计划是哪一条噢。比如您可以说：' + '我要更改' + self.old_event.day_des_gen() 
			rst += self.old_selftime if oldtime is True else ''
			rst += tmp + '开始的' + self.old_detail + '计划。'
			check = False

		return event, rst, check



	def __selftime_update(self, event):
		event = event[0]
		starthour, startminute = event.starthour(), event.startminute()
		endhour, endminute = event.endhour(), event.endminute()
		old_duration = event.duration()

		startime = datetime(self.new_year, self.new_month, self.new_day, starthour, startminute, 0)
		endtime = datetime(self.new_year, self.new_month, self.new_day, endhour, endminute, 0) if self.new_event.get_duration() is None \
		else self.new_event.get_duration() + startime
		new_duration = endtime - startime

		self.old_event = Event(year=self.old_year, month=self.old_month, day=self.old_day, hour=starthour, minute=startminute,
			duration=old_duration)
		self.new_event = Event(year=self.new_year, month=self.new_month, day=self.new_day, hour=starthour, minute=startminute,
			duration=new_duration)
		
		try:
			event.startTime = startime
			event.endTime =  endtime 
			event.agendaDetail, event.agendaType = self.new_detail, self.new_detail
			self.db.session.commit()
		except Exception as err:
			self.__log_error(err)
			rst = "抱歉，我找到了您要更改的计划，只是现在规划本出了点问题，更改失败了..."
			return rst

		rst = '更改成功！已经将您' + self.old_event.day_des_gen() + self.old_event.time_des_gen() + '的' + self.old_detail + '计划，更改'
		if self.new_detail is not None and self.new_detail != self.old_detail:
			rst += '为' + self.new_event.day_des_gen() + self.new_event.time_des_gen() + '开始的' + self.new_detail + '计划，'
		else:
			rst += '到' + self.new_event.day_des_gen() + self.new_event.time_des_gen() + '，'

		rst += '预计在' + self.new_event.day_des_gen(False) + self.new_event.time_des_gen(False) + '结束。'
		return rst




	def __selftimes(self):
		event, rst, check = self.__query_selftime()
		if check is False:
			return rst
		if self.new_selftime != self.old_selftime:
			old_des = self.old_event.day_des_gen()
			new_des = self.new_event.day_des_gen()
			rst = '更改失败了噢。请您告诉我新计划的具体时间。比如您可以说：把' + old_des + self.old_selftime + '的' +\
			self.old_detail + '改到' + new_des + self.new_selftime
			tmp = '8点。' if (self.new_selftime == '上午' or self.new_selftime == '晚上') else '5点半。'
			rst += tmp
		else:
			rst = self.__selftime_update(event)

		return rst
	

	def __old_selftime(self):
		event, rst, check = self.__query_selftime()
		if check is False:
			return rst
		#event = event[0]
		#hour, minute = event.starthour(), event.startminute()
		#domain = self.__check_ts(hour, minute)
		#if domain == self.new_selftime:
		rst = self.__selftime_update(event)
		# else:
		# 	event = event.make_event()
		# 	des = event.day_des_gen() + self.old_selftime + '的' + self.old_detail + '计划'
		# 	rst = '更改失败了噢，您原来的' + self.old_detail + '计划是在' + event.day_des_gen() + event.time_des_gen() + '，请问您要将'
		# 	rst += '新计划改到' + self.new_event.day_des_gen() +  '的什么时候呢？比如您可以说，将' + des
		# 	rst += '改为' if self.old_detail != self.new_detail else '改到'
		# 	rst += self.new_event.day_des_gen() + self.old_selftime
		# 	rst += '的' + self.new_detail + '计划。' if self.old_detail != self.new_detail else '。'

		return rst


	def __multiples(self):
		query = self.db.session.query(Agenda).filter(and_(
			Agenda.jdID==self.jdID, 
			extract('year', Agenda.startTime) == self.old_event.get_year(),
			extract('month', Agenda.startTime) == self.old_event.get_month(),
			extract('day', Agenda.startTime) == self.old_event.get_day(),
			Agenda.agendaDetail == self.old_event.get_detail()))
		events = query.all()
		if len(events) == 0:
			rst = '更改失败了噢，您' + self.old_event.day_des_gen() + self.old_event.time_des_gen() + \
			'并没有' + self.old_event.get_detail() + '这条计划。请您先添加噢。'
		elif len(events) > 1:
			rst = '您在' + self.old_event.day_des_gen() + '有' + str(len(events)) + '条相似计划。开始时间分别为：'
			for e in events:
				a = e.make_event()
				rst += a.day_des_gen() + a.time_des_gen() + "。"
			rst += '请问您要更改哪一条呢？'
		else:
			try:
				event = query.first()
				if self.new_event.get_startime() is None:
					event.endTime = self.new_event.get_duration() + event.startTime
				else:
					event.startTime = self.new_event.get_startime()
					event.endTime = self.new_event.get_duration() + self.new_event.get_startime()
				event.agendaDetail = self.new_event.get_detail()
				self.db.session.commit()
			except Exception as err:
				self.__log_error(err)
				rst = "抱歉，我找到了您要更改的计划，只是现在出了点问题，更改失败了..."
				return rst

			rst = '更改成功！新的' + self.new_event.get_detail() + '时间为' + self.new_event.day_des_gen() + \
			self.new_event.time_des_gen() + '，预计需要' + self.new_event.duration_des_gen() + '，' + \
			'结束时间为' + self.new_event.day_des_gen(start=False) + self.new_event.time_des_gen(start=False) + \
			'。'
		return rst


	def __singles(self):
		event = self.db.session.query(Agenda).filter(and_(
			Agenda.jdID==self.jdID, extract('year', Agenda.startTime) == self.old_event.get_year(),
			extract('month', Agenda.startTime) == self.old_event.get_month(),
			extract('day', Agenda.startTime) == self.old_event.get_day(),
			extract('hour', Agenda.startTime) == self.old_event.get_hour(),
			extract('minute', Agenda.startTime) == self.old_event.get_minute(),
			Agenda.agendaDetail == self.old_event.get_detail())).first()
		if not event:
			rst = '更改失败了呢，规划本没有找到' + self.old_event.day_des_gen() + self.old_event.time_des_gen() + \
			'的' + self.old_event.get_detail() + '计划。请您先进行添加哈。'
		else:
			try:
				event.startTime = self.new_event.get_startime()
				event.endTime = self.new_event.get_endtime()
				event.agendaDetail = self.new_event.get_detail()
			except Exception as err:
				self.__log_error(err)
				rst = "抱歉，我找到了您要更改的计划，只是现在出了点问题，更改失败了..."
				return rst

			rst = '更改成功！新的' + self.new_event.get_detail() + '时间为' + self.new_event.day_des_gen() + \
			self.new_event.time_des_gen() + '，预计需要' + self.new_event.duration_des_gen() + '，' + \
			'结束时间为' + self.new_event.day_des_gen(start=False) + self.new_event.time_des_gen(start=False) + \
			'。'
		return rst
		

	def __log_error(self, err):
		f = open('err/update.err', 'a')
		f.write(str(err))
		f.write('\n')
		f.write('\n')
		f.close()


	def update(self):
		rst = self.__which_update()
		return rst