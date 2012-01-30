#!/usr/bin/env python

from uvscada.dylos.dc1100 import *
import unittest

class DylosTest(unittest.TestCase):
	def setUp(self):
		pass
		
	def test_parse(self):
		#project = PTOProject.parse_from_file_name('in.pto')
		#self.assertTrue(project.text != None)
		#self.assertEqual(len(project.image_lines), 4)
		m = Measurement.parse('123,45')
		self.assertEqual(m.small, 123)
		self.assertEqual(m.large, 45)

	def test_pro(self):
		d = DC1100Pro(None)
	
	def test_quality(self):
		d = DC1100Pro(None)
		self.assertEqual(d.quality(), None)
		m = Measurement(123, 45)
		d.last_meas = m
		self.assertEqual(d.quality_str(), 'VERY_GOOD')
    	
	def test_cpm(self):
		'''
		0.01 cubic foot to meters
		
		Say reading is 1 =. 1 particle / (0.01 ft**3)
		1 particle / ft**3 * 100 = 100 ft**3
		= 100 particles / (1 ft * 12 inch / ft * 25.4 mm / inch * 1 m / 1000 mm)**3 
		= 100 particles / (0.3048 m)**3 
		= 100 particles / (0.028316847 * m**3)
		= 3531.466672 particles / m**3
		
		'''
		p = 3531.466672
		m = Measurement(100, 1)
		print 'Small CPM: %f' % m.small_cpm()
		print 'Large CPM: %f' % m.large_cpm()
		self.assertTrue(abs(m.small_cpm() - 100.0 * p) < 1.0 )
		self.assertTrue(abs(m.large_cpm() - p) < 1.0 )
	
if __name__ == '__main__':
	unittest.main()

