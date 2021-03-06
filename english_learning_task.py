# import hashlib
import os
import time

import xmltodict
from apscheduler.schedulers.background import BackgroundScheduler
from flask import Flask, request, render_template
from flask_apscheduler import APScheduler
from gevent import pywsgi

from db import *
from util import *

app = Flask(__name__)
scheduler = APScheduler(scheduler=BackgroundScheduler(timezone='Asia/Shanghai'))

handles, wechat_ids = {}, {}
verification_code = generate_verification_code()
data = {}

WECHAT_TOKEN = 'test'

BEGIN_TIME = '000000'
END_TIME = '235930'


def init():
    users = get_all_users()
    if not users:
        return
    for user in users:
        wechat_id, handle = user
        wechat_ids[wechat_id] = handle
        handles[handle] = wechat_id


@scheduler.task('cron', id='timer', day='*', hour='23', minute='59', second='50')
def generate_report():
    command1 = 'wget --output-document=%s.html huanhuacf.top/record' % get_date()
    command2 = 'mv %s.html templates/report/' % get_date()
    os.system('%s && %s' % (command1, command2))
    data.clear()


def register(message: str, wechat_id: str) -> str:
    global verification_code
    n = len(message)
    low = high = 0
    for i in range(n):
        if message[i] == ' ':
            low = i
            break
    for i in range(n - 1, -1, -1):
        if message[i] == ' ':
            high = i
            break
    password = message[high + 1:]
    if password != verification_code:
        return 'Wrong password. Please contact the administrator.'
    verification_code = generate_verification_code()
    handle = message[low + 1:high]
    if not handle:
        return 'Handle should have a minimum length of 1. Try again.'
    if handle in handles:
        return 'Username "%s" already taken, Please use another username.' % handle
    elif wechat_id in wechat_ids and wechat_ids[wechat_id] != handle:
        old_handle = wechat_ids[wechat_id]
        wechat_ids[wechat_id] = handle
        handles[handle] = wechat_id
        handles.pop(old_handle)
        update_user(wechat_id, handle)
        return 'You changed your handle from "%s" to "%s".' % (old_handle, handle)
    else:
        wechat_ids[wechat_id] = handle
        handles[handle] = wechat_id
        add_user(wechat_id, handle)
        return 'Congratulations! You have registered successfully! Your handle is "%s".' % handle


def check_in(wechat_id: str, url: str) -> str:
    if not BEGIN_TIME <= get_time() <= END_TIME:
        return '???????????????????????????'
    if wechat_id not in wechat_ids:
        return 'You haven\'t registered yet. Please contact the administrator.'
    if wechat_id not in data:
        data[wechat_id] = [[url, get_time()]]
    else:
        data[wechat_id].append([url, get_time()])
    count_record = len(data[wechat_id])
    reply = '????????????: %d\n??????: %s\n' % (count_record, url)
    if count_record >= 2:
        reply += '\n?????????????????????????????????, ????????????huanhuacf.top/record ????????????????????????????????????????????????????????????????????????????????????????????????????????????????????????????????????\n\n%s' % os.popen('fortune').read()
    return reply


@app.route('/password')
def get_verification_code() -> str:
    return render_template('message.html', message=verification_code, title='Password')


@app.route('/rule')
def hello_world():
    return 'Hello World!'


@app.route('/unregister/<handle>')
def unregister(handle):
    flag = False
    if handle in handles:
        wechat_id = handles[handle]
        if wechat_id in data:
            data.pop(wechat_id)
        remove_user(handle)
        handles.pop(handle)
        flag = True
    if flag:
        message = 'User "%s" deleted.' % handle
    else:
        message = 'There is no user with handle %s.' % handle
    return render_template('message.html', message=message, title='Delete user')


@app.route('/users')
def show_all_users():
    users = []
    for handle, _ in handles.items():
        users.append(handle)
    return render_template('users.html', users=users)


@app.route('/report/<date>')
def get_report(date: str):
    return render_template('report/%s.html' % date)


@app.route('/record')
def statistics():
    records = {}
    lazy_people = set()
    for wechat_id, v in data.items():
        handle = wechat_ids[wechat_id]
        if len(v) < 2:
            lazy_people.add(handle)
        else:
            t = []
            for i in range(len(v) - 2, len(v)):
                if BEGIN_TIME <= v[i][1] <= END_TIME:
                    t.append(v[i][0])
            if len(t) == 2:
                records[handle] = t
            else:
                lazy_people.add(handle)
    for handle in handles:
        if handle not in records:
            lazy_people.add(handle)
    return render_template('record.html', records=records, lazy_people=list(lazy_people))


@app.route('/wechat', methods=['GET', 'POST'])
def wechat():
    # args = request.args
    #
    # signature = args.get('signature')
    # timestamp = args.get('timestamp')
    # nonce = args.get('nonce')
    # echostr = args.get('echostr')
    #
    # temp = [WECHAT_TOKEN, timestamp, nonce]
    # temp.sort()
    # temp = "".join(temp)
    # m = hashlib.sha1()
    # m.update(temp.encode('utf8'))
    # sig = m.hexdigest()
    #
    # if sig == signature:
    #     if request.method == "GET":
    #         return echostr
    # else:
    #     return 'errno', 403

    data_received = request.data
    d = xmltodict.parse(data_received).get('xml')
    message_type = d.get('MsgType')
    response = {
        "ToUserName": d.get('FromUserName'),
        "FromUserName": d.get('ToUserName'),
        "CreateTime": int(time.time()),
        "MsgType": "text",
    }
    if message_type == 'text':
        content = d.get('Content')
        if len(content) >= 3:
            if content[:2] == 's ':
                key = d.get('Content')[2:]
                response['Content'] = search(key)
            elif content[:2] == 'r ':
                response['Content'] = register(content, d.get('FromUserName'))
            elif content[:2] == 'c ':
                url = content[2:]
                response['Content'] = check_in(d.get('FromUserName'), url)
        else:
            response['Content'] = 'Sorry, please try again.'
    elif message_type == 'image':
        pic_url = d.get('PicUrl')
        response['Content'] = check_in(d.get('FromUserName'), pic_url)

    response = {"xml": response}
    return xmltodict.unparse(response)


if __name__ == '__main__':
    init()
    scheduler.init_app(app)
    scheduler.start()
    server = pywsgi.WSGIServer(('0.0.0.0', 8001), app)
    server.serve_forever()
