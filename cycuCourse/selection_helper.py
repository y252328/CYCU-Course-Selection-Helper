# -*- coding: utf-8 -*-
"""
CYCU coures selection helper

Version: 1.0.0
"""
import datetime
import threading
import sched
import time

from cycuCourse import CycuCourse


startTime = {'hour': 22, 'minute': 0,
             'second': 1, 'microsecond': 0}  # 搶課系統開啟時間
offset = 5  # 提前時間

welcome = """**********************************
* 歡迎使用中原選課小幫手         *
* 請輸入 help 將會有進一步的說明 *
**********************************"""

help = '''login  : 登入選課系統
l      : 快速登入(使用預設帳號)
set time : 設定開始選課時間
show time : 顯示開始選課時間
check  : 確認是否有登入
list   : 列出已選到課程
del course : 退選已選上的課(不可逆操作，請謹慎使用)
del append : 取消遞補(不可逆操作，請謹慎使用)
summory: 列出欲加選課程清單
add    : 增加欲加選課程
del    : 刪除所有欲選課程
run    : 執行自動加選
cancel : 取消自動加選
logout : 登出選課系統
exit   : 離開程式
'''


def printList(list_):
    """course list formatted output.

    Args:
        list_ (list): course list.
    """
    for i, oneCourse in enumerate(list_):
        cname = oneCourse.get('cname', '')
        teacher = oneCourse.get('teacher', '')
        op_time_1 = oneCourse.get('op_time_1', '')
        op_time_2 = oneCourse.get('op_time_2', '')
        if op_time_2 == None:
            op_time_2 = ''
        print('{}\t{}\t{}\t{}\t{}\t{}'.format(i, oneCourse['op_code'],
                                              cname, teacher, op_time_1, op_time_2))


def selectAll(event, cc, account, course_list, list_lock, count=-1, intervals=(0.3333333333, 0.5)):
    """This is a callback function that call by sched to select courses in course_list

    Args:
        event (event): stop flag.
        cc (CycuCourse): CycuCourse object
        account (str,str): student id and password
        course_list (list): coures list
        list_lock (lock): list lock
        count (int): add seletion times, -1 for inf.
        intervals (int, int): (try login interval, selection interval)
    """
    print('start select')
    i = 0
    while not cc.login(*account) and not event.is_set():
        time.sleep(intervals[0])  # try login delay

    while (not event.is_set()) and count != 0:
        print('count : {}'.format(count))
        list_lock.acquire()
        if len(course_list) > 0:
            op_code = course_list[i % len(course_list)]['op_code']
            if cc.addSelection(op_code):
                del course_list[i % len(course_list)]
            else:
                i += 1
            list_lock.release()
        else:
            list_lock.release()
            break
        time.sleep(intervals[1])
        if count > 0:
            count -= 1

    if not event.is_set():
        event.set()


def cli():
    global startTime
    uid, pwd = '', ''
    cc = CycuCourse()
    tt = None  # thread for perform addSeletion
    ss = sched.scheduler(cc.time, time.sleep)
    list_lock = threading.Lock()
    ee = threading.Event()  # tt stop flag, false for stop
    ee.set()
    course_list = []
    exit_ = False
    #print('Welcome to use CYCU course seletion helper')
    print(welcome)
    while not exit_:
        cmd = input('>')
        cmd = cmd.strip()
        if cmd == 'login':
            uid = input('Plz enter id : ')
            pwd = input('Plz enter password : ')
            cc.login(uid.strip(), pwd.strip())
        elif cmd == 'l':
            cc.login(uid, pwd)
        elif cmd == 'logout':
            cc.logout()
        elif cmd == 'adds':
            op_code = input('Plz enter course code : ')
            full_info = cc.search(op_code)
            if full_info != None:
                list_lock.acquire()
                course_list.append(full_info)
                list_lock.release()
            else:
                print('找不到QQ')
            printList(course_list)
        elif cmd == 'add':
            op_code = input('Plz enter course code : ')
            course_info = {'op_code': op_code}
            course_list.append(course_info)
            printList(course_list)
        elif cmd == 'list':
            printList(cc.listCourse())
        elif cmd == 'del course':
            op_code = input('Plz enter course code : ')
            cc.deleteSelection(op_code)
        elif cmd == 'del append':
            op_code = input('Plz enter course code : ')
            cc.deleteAppend(op_code)
        elif cmd == 'summory':
            print('start time : ', end='')
            print(startTime)
            printList(course_list)
        elif cmd == 'check':
            print('成功' if cc.check() else '失敗')
        elif cmd == 'del':
            list_lock.acquire()
            course_list.clear()
            list_lock.release()
        elif cmd == 'run':
            if ee.is_set():
                ee.clear()
                print('start scheduler')
                tt = threading.Thread(target=ss.run)
                now = datetime.datetime.fromtimestamp(cc.time())
                startTime = now.replace(**startTime)
                ss.enterabs((startTime.timestamp()-offset), 1, selectAll,
                            (ee, cc, (uid, pwd,), course_list, list_lock))
                # ss.run()
                tt.start()
            else:
                print('已經開始')
        elif cmd == 'cancel':
            print('cancel')
            ee.set()
            for e in ss.queue:
                ss.cancel(e)
        elif cmd == 'exit':
            if ee.is_set():
                exit_ = True
            else:
                print('Plz cancel scheduler first')
        elif cmd == 'set time':
            newTime = {'microsecond':0}
            try:
                newTime['hour'] = int(input('Hour : '))
                newTime['minute'] = int(input('Min : '))
                newTime['second'] = int(input('Second : '))
                now = datetime.datetime.fromtimestamp(cc.time())
                newTimeStamp = now.replace(**newTime).timestamp()
                if newTimeStamp > now.timestamp():
                    startTime = newTime
                else:
                    print('New time before NOW')
            except:
                print('Failed to set time')
        elif cmd == 'show time':
            print('Run at {:02}:{:02}:{:02}'.format(
                startTime['hour'], startTime['minute'], startTime['second']))
        elif cmd == 'help':
            print(help)
        elif cmd: # unknow command exclude empty command
            print('指令錯誤，如需幫助請輸入"help"!')

    del cc
    del ss
    del ee
    del list_lock
    del tt
    print('Bye Bye')


if __name__ == '__main__':
    cli()
