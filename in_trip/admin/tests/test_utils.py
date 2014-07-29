#encoding=utf-8
import unittest

from in_trip.lib.http import get_domain

class TestUtilsFunc(unittest.TestCase):
    def setUp(self):
        self.case_url = [
                ('python.org', 'http://docs.python.org/2/library/unittest.html'),
                ('google.com', 'google.com'),
                ('sina.com.cn', 'http://www.sina.com.cn/'),
                ]

    def test_get_domain(self):
        for domain, url in self.case_url:
            self.assertEqual(domain, get_domain(url))



if __name__ == '__main__':
    unittest.main()
