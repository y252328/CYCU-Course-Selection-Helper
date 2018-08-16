# -*- coding: utf-8 -*-
"""
CYCU coures selection API

Version: 1.0.0
"""
import sys
import time
import requests
import json

from cycuCourse import crypto


class CycuCourse():
    def __init__(self, outStream=sys.stdout):
        """Initial function

        Args:
            outStream (filelike): The stream to output.
        """
        self.s = None
        self.headers = {
            'Accept': '*/*',
            'Accept-Encoding': 'gzip, deflate',
            'Accept-Language': 'zh-TW,zh;q=0.9,en-US;q=0.8,en;q=0.7',
            'Connection': 'keep-alive',
            'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8',
            'Host': 'csys.cycu.edu.tw',
            'Origin': 'http://csys.cycu.edu.tw',
            'Referer': 'http://csys.cycu.edu.tw/student/',
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/63.0.3239.108 Safari/537.36',
        }
        self.login_time = None
        self.outStream = outStream
        self._syncTime()

    def isLogin(self):
        """Check Status

        Returns:
            bool: The return value. True for success, False otherwise.
        """
        if self.s == None:
            return False
        elif self.login_time != None and time.time() - self.login_time > 295:
            self.print('Timeout, re-login...')
            self.logout(True)
            return self.login(self._userId, self._password)

        return True

    def login(self, userId, password):
        """Login function.

        Args:
            userId (str): Studen ID.
            password (str): password.

        Returns:
            bool: The return value. True for success, False otherwise.
        """
        self._userId, self._password = userId, password
        if self.isLogin():
            self.logout()
        self.s = requests.Session()
        r_log_init = self.s.request(
            'POST', url='http://csys.cycu.edu.tw/student/sso.srv', headers=self.headers, data={'cmd': 'login_init'})
        j_log_init = json.loads(r_log_init.text)

        if not j_log_init['result']:
            self.print(j_log_init['message'])
            self.s = None
            return False
        secureRandom = j_log_init['secureRandom']

        userid, password = crypto(userId.encode(
            'ascii'), password.encode('ascii'), secureRandom.encode('ascii'))
        r_log = self.s.request('POST',  url='http://csys.cycu.edu.tw/student/sso.srv',
                               headers=self.headers, data={'cmd': 'login', 'userid': userid, 'hash': password})
        if r_log.status_code == 200:
            j_log = json.loads(r_log.text)
            self.print(j_log['message'])
            if j_log['result']:
                self._updateLoginT()
                self.headers['Page-Id'] = j_log['pageId']
            else:
                self.s.close()
                self.s = None

            # self._syncTime()
            return j_log['result']

        self.s = None
        return False

    def logout(self, force=False):
        """Logout funtion.

        Args:
            force (bool): logout without check status if force is true.
        """
        if self.s != None:
            if force:
                r_logout = self.s.request(
                    "POST", url='http://csys.cycu.edu.tw/student/sso.srv', headers=self.headers, data={'cmd': 'logout'})
                j_logout = json.loads(r_logout.text)
            elif self.isLogin():
                r_logout = self.s.request(
                    "POST", url='http://csys.cycu.edu.tw/student/sso.srv', headers=self.headers, data={'cmd': 'logout'})
                j_logout = json.loads(r_logout.text)
                self.print(j_logout['message'])
            self.s.close()
            self.s = None
        self.login_time = None

    def check(self):
        """Check login and network status"""
        if self.isLogin():
            r_check = self.s.request("POST", url='http://csys.cycu.edu.tw/student/sso.srv',
                                     headers=self.headers, data={'cmd': 'checkPageId'})
            j_check = json.loads(r_check.text)
            if r_check.status_code == 200:
                self._updateLoginT()
            return j_check['result']
        else:
            self.print('請先登入')
            return False

    def listCourse(self):
        """List selected courses."""
        if not self.isLogin():
            self.print('請先登入')
            return None
        else:
            url_selection = 'http://csys.cycu.edu.tw/student/student/op/StudentCourseView.srv'
            data = {
                'cmd': 'selectJson',
                'where': ('sn_status>0 AND idcode={}'.format(self._userId)),
                'orderby': 'sn_course_type,op_code'}
            r_select = self.s.request(
                "POST", url=url_selection, headers=self.headers, data=data)
            if r_select.status_code == 200:
                j_select = json.loads(r_select.text)
                return j_select['datas']
        return None

    def search(self, op_code):
        """Search course.

        Args:
            op_code (str): op code of course.

        Returns:
            json: course info.
            None: return None if search failed
        """
        if not self.isLogin():
            self.print('請先登入')
            return None
        else:
            url_selection = 'http://csys.cycu.edu.tw/student/student/op/StudentCourseView.srv'
            data = {
                'cmd': 'selectJson',
                'where': ("(op_code LIKE '{}')".format(op_code)),
                'orderby': 'sn_course_type,op_code',
                'length': 1}
            r_select = self.s.request(
                "POST", url=url_selection, headers=self.headers, data=data)
            if r_select.status_code == 200:
                j_select = json.loads(r_select.text)
                if j_select['totalRows'] > 0:
                    return j_select['datas'][0]
        return None

    def addTrace(self, op_code):
        """Add course to trace list.(加入追蹤)

        Args:
            op_code (str): op code of course.

        Return:
            bool: True for success, False otherwise.
        """
        return self.Trace(op_code, True)

    def deleteTrace(self, op_code):
        """Delete course from trace list.(刪除追蹤)

        Args:
            op_code (str): op code of course.

        Return:
            bool: True for success, False otherwise.
        """
        return self.Trace(op_code, False)

    def Trace(self, op_code, add):
        """Delete of add course from trace list.(加入/刪除追蹤)

        Args:
            op_code (str): op code of course.
            add (bool): True for add, False for delete

        Return:
            bool: True for success, False otherwise.
        """
        if not self.isLogin():
            self.print('請先登入')
            return False
        else:
            self.print('{}追蹤 "{}"...'.format(
                (''if add else '取消'), op_code))
            url_trace = 'http://csys.cycu.edu.tw/student/student/op/StudentCourseTrace.srv'
            cmd = 'insert' if add else 'delete'
            r_insert = self.s.request("POST", url=url_trace, headers=self.headers, data={
                                      'cmd': cmd, 'op_code': op_code})
            if r_insert.status_code == 200:
                self._updateLoginT()
                j_insert = json.loads(r_insert.text)
                if j_insert['result']:
                    self.print('成功')
                else:
                    self.print('失敗')
                return j_insert['result']
            else:
                self.print('失敗!')
                return False

    def addSelection(self, op_code):
        """Add selection course.(加選)

        Args:
            op_code (str): op code of course.

        Return:
            bool: True for success, False otherwise.
        """
        return self.Selection(op_code, True)

    def deleteSelection(self, op_code):
        """Delete selection course.(退選)

        Args:
            op_code (str): op code of course.

        Return:
            bool: True for success, False otherwise.
        """
        return self.Selection(op_code, False)

    def Selection(self, op_code, add):
        """ADD of Delete selection course.(加/退選)

        Args:
            op_code (str): op code of course.
            add (bool): True for add, False for delete

        Return:
            bool: True for success, False otherwise.
        """
        if not self.isLogin():
            self.print('請先登入')
            return False
        else:
            self.print('{}選 "{}"...'.format(('加'if add else '退'), op_code))
            url_selection = 'http://csys.cycu.edu.tw/student/student/op/StudentCourseView.srv'
            cmd = 'addSelection' if add else 'deleteSelection'
            r_select = self.s.request("POST", url=url_selection, headers=self.headers, data={
                                      'cmd': cmd, 'op_code': op_code})
            if r_select.status_code == 200:
                j_select = json.loads(r_select.text)
                self.print(j_select['message'])
                if '已在原遞補清單中' in j_select['message']:
                    return True
                return j_select['result']
            else:
                self.print('加退選失敗 !')
                return False

    def deleteAppend(self, op_code):
        """Delete Append course.(取消遞補)

        Args:
            op_code (str): op code of course.

        Return:
            bool: True for success, False otherwise.
        """
        if not self.isLogin():
            self.print('請先登入')
            return False
        else:
            self.print('取消遞補 "{}"...'.format(op_code))
            url_selection = 'http://csys.cycu.edu.tw/student/student/op/StudentCourseView.srv'
            cmd = 'deleteAppend'
            r_select = self.s.request("POST", url=url_selection, headers=self.headers, data={
                                      'cmd': cmd, 'op_code': op_code})
            if r_select.status_code == 200:
                j_select = json.loads(r_select.text)
                self.print(j_select['message'])
                return j_select['result']
            else:
                self.print('取消遞補 !')
                return False

    def time(self):
        """Get time of selection system.(取得選課系統時間)

        Return:
            int: timestamp of selection system(unit:sec.).
        """
        return time.time() + self._diff

    def print(self, *args, **kwargs):
        """Custom Print that output to cycuCourse.outStream
        """
        kwargs['file'] = self.outStream
        print(*args, **kwargs)

    def _updateLoginT(self):
        self.login_time = time.time()

    def _syncTime(self):
        r_time = requests.get(
            'http://csys.cycu.edu.tw/student/', headers=self.headers)
        t1 = time.time()
        start = r_time.text.find('window.serverTime = ')+20
        end = r_time.text.find(';', start)
        self._diff = (int(r_time.text[start:end])/1000) - t1
        #print('sync time')

    def __del__(self):
        self.logout()


if __name__ == '__main__':
    """Example code"""
    cc = CycuCourse()  # creat CycuCourse object
    cc.login('id', 'password')  # login
    cc.addSelection('CS413L')  # 加選CS413L
    cc.deleteAppend('CS413L')  # 取消遞補CS413L
    cc.deleteSelection('GE275C')  # 退選GE275C
