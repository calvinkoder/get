import math
import time

class Unit:
	baseUnit = ''
	defaultVal = 0

	def __init__(self, val = None):
		if not val:
			val = self.defaultVal
		if isinstance(val, Unit):
			val = val.rawVal
		self.unit = self.baseUnit
		self.rawVal = val
		self.val = val

	def __str__(self):
		return '{0:.2f}{1}'.format(self.val, self.unit)

	"""
	Arithmetic operators
	"""
	def __add__(self, other):
		if isinstance(other, Unit):
			return self.__class__(self.rawVal + other.rawVal)
		return self.__class__(self.rawVal + other)
		
	def __sub__(self, other):
		if isinstance(other, Unit):
			return self.__class__(self.rawVal - other.rawVal)
		return self.__class__(self.rawVal - other)
		
	def __mul__(self, other):
		if isinstance(other, Unit):
			return self.__class__(self.rawVal * other.rawVal)
		return self.__class__(self.rawVal * other)
		
	def __truediv__(self, other):
		if isinstance(other, Unit):
			return self.__class__(self.rawVal / other.rawVal)
		return self.__class__(self.rawVal / other)

class MetricUnit(Unit):
	def __init__(self, val):
		Unit.__init__(self, val)
		if self.val == 0:
			return

		power = math.floor(math.log(val, self.interval))
		self.val = val / self.interval**(power)
		self.unit = self.prefixes[power]+self.baseUnit

class AbsoluteUnit(MetricUnit):
	def __init__(self, val):
		if val < 0:
			Unit.__init__(self, val)
			return
		MetricUnit.__init__(self, val)

class CustomUnit(Unit):
	def __init__(self, val):
		Unit.__init__(self, val)
		if self.rawVal == 0:
			self.vals = [(0, self.baseUnit)]
			return

		val = self.val

		self.vals = []

		for unit, scale in self.units:
			if val > 0:
				_val = (val % scale)
				self.vals.append((_val, unit))
				val -= _val
				val /= scale

		if val > 0:
			self.vals.append((val, self.finalUnit))

	def __str__(self):
		return ''.join(reversed(['{0:.0f}{1}'.format(val, unit) for val, unit in self.vals]))

"""
Specific Units
"""
class Data(AbsoluteUnit):
	baseUnit = 'B'
	prefixes = ['', 'k', 'M', 'G', 'T']
	interval = 10**3

class Time(CustomUnit):
	baseUnit = 's'
	units = (
		('s', 60),
		('min', 60),
		('hr', 24),
		('day', 364.25)
	)
	finalUnit = 'year'

class CurrentTime(Time):
	def __init__(self, val = None):
		Time.__init__(self, val)

	@property
	def defaultVal(self):
		return time.time()
	
class Percent(Unit):
	baseUnit = '%'

class Rate(Unit):
	otherUnit = Time(0)
	def __init__(self, a, b):
		if b.val == 0:
			self.mainUnit = a
		else:
			self.mainUnit = (a / b)
			
		self.rawVal = self.mainUnit.rawVal
		self.val = self.mainUnit.val

	@property
	def unit(self):
		return '{0}/{1}'.format(self.mainUnit.unit, self.otherUnit.baseUnit)

class Progress:
	def __init__(self, progress, total, startTime = None):
		self.progress = progress
		self.total = total
		if not startTime:
			self.startTime = CurrentTime()

	def duration(self):
		return CurrentTime() - self.startTime

	def rate(self):
		return Rate(self.progress, self.duration())

	def timeLeft(self):
		try:
			return Time((self.total - self.progress) / self.rate())
		except ZeroDivisionError:
			return 'Infinite'

	def __str__(self, estimates = True):
		clearLine = '\r\033[2K'

		progress = '{0}/{1}'.format(self.progress, self.total)
		duration = 'Time:{0}'.format(self.duration())
		strs = [progress, duration]

		if estimates:
			rate = 'Rate:{0}'.format(self.rate())
			timeLeft = 'Time Left:{0}'.format(self.timeLeft())
			strs += [rate, timeLeft]

		return clearLine+', '.join(strs)