# -*- coding: utf-8 -*-
from datetime import datetime
from PIL import Image
import json
import os
import sys
import requests
import time
import re


# 当前运行目录
BASE_DIR = os.path.dirname('.')
# 设定信息
SETTING = {}

# 加载json
def load_setting(filename='setting.json'):
    global SETTING
    with open(os.path.join(BASE_DIR, filename), 'r') as file:
        SETTING = json.load(file)

# 获取账号信息
def get_ym_info():
    token = SETTING['ym']['token']
    info_url = 'http://api.fxhyd.cn/UserInterface.aspx?action=getaccountinfo&token=' + token
    result = requests.get(info_url).text.split('|')
    format = 'success|用户名|账户状态|账户等级|账户余额|冻结金额|账户折扣|获取号码最大数量'.split('|')
    for i in range(len(format)):
        if i == 0:
            continue
        else:
            result[i] = format[i] + ":" + result[i]
    return ';'.join(result)

# 获取手机号码
def get_eostoken_phone():
    token = SETTING['ym']['token']
    project_id = SETTING['ym']['project_id']
    phone_url = ('http://api.fxhyd.cn/UserInterface.aspx?action=getmobile&itemid='
                    + project_id + '&token=' + token)
    result = requests.get(phone_url).text.split('|')
    if len(result) == 1:
        raise Exception('错误：余额不足')
    else:
        return result[1]

# 释放号码
def release_candy_phone(phone):
    token = SETTING['ym']['token']
    project_id = SETTING['ym']['project_id']
    phone_url = ('http://api.fxhyd.cn/UserInterface.aspx?action=release&mobile='
                    + phone + '&itemid=' + project_id + '&token=' + token)
    result = requests.get(phone_url).text
    return True if result == 'success' else False

# 获取短息验证码
def get_sms_code(phone):
    token = SETTING['ym']['token']
    project_id = SETTING['ym']['project_id']
    sms_url = ('http://api.fxhyd.cn/UserInterface.aspx?action=getsms&mobile=' 
                + phone +' &itemid=' + project_id + '&token=' + token)
    log('获取短信：' + phone)
    result = requests.get(sms_url).text.split('|')
    count = 1
    while len(result) == 1:
    	log('第' + str(count) + '次获取验证码')
    	if count >= SETTING['ym']['retest']:
    		return ''
    	time.sleep(3)
    	result = requests.get(sms_url).text.split('|')
    	count += 1

    group = re.findall('\d+', result[1])
    if len(group) == 1:
    	log('验证码：' + group[0])
    	return group[0]
    else:
    	raise Exception('错误：' + result[1] + '未能找到有效验证码')

# eostoken验证短信验证码
def send_code(phone, code):
	params = {
		'phone': phone,
		'code': code
	}
	# proxies = {
	# 	"http": "http://127.0.0.1:8060"
	# }
	# r = requests.get('http://api.eostoken.im/capture1', params=params, proxies=proxies)
 	r = requests.get('http://api.eostoken.im/capture1', params=params)
	result = json.loads(r.text)
	log(result)
	return True if result['msg'] == 'success' else False

# eostoken设置账号密码
def set_password(phone, code):
	params = {
		'phone': phone,
		'code': code,
		'invite': SETTING['eostoken']['inviter_id'],
		'password': SETTING['eostoken']['password']
	}
	r = requests.get('http://api.eostoken.im/register1/', params=params)
	result = json.loads(r.text)
	log(result)
	return True if result['msg'] == 'success' else False

# 获取图片验证码
def get_code_image(phone):
	r = requests.post('http://api.eostoken.im/kapimg/' + phone)
	with open(os.path.join(BASE_DIR, 'code.png'), 'wb') as file:
		file.write(r.content)
	# load
	img = Image.open(os.path.join(BASE_DIR, 'code.png'))
	img.show()


# eostoken设置账号密码
def save_passcount(phone):
	filename = SETTING['log_file']
	line_text = phone + '/' + SETTING['eostoken']['password']
	with open(os.path.join(BASE_DIR, filename), 'a+', encoding='utf-8') as file:
		file.writelines(line_text + '\n')
	log(line_text)

def log(text):
	now = datetime.now()
	print(datetime.strftime(now, '%H:%M:%S') + ': ' + str(text))


if __name__ == '__main__':

	log('Start load setting.json')
	load_setting()
	log(get_ym_info())

	while True:
		try:
			phone = get_eostoken_phone()
			log('成功获取手机号码：' + phone)
			get_code_image(phone)
			log('成功获取图片验证码')
			code = input('输入图片验证码：')
			if not send_code(phone, code):
				release_candy_phone(phone)
				log('重新释放手机号码：' + phone)
				continue
			code = get_sms_code(phone)
			if code == '':
				release_candy_phone(phone)
				log('重新释放手机号码：' + phone)
				continue
			if set_password(phone, code):
				save_passcount(phone)
			else:
				log('用户名已存在：' + phone)
			# 释放号码
			release_candy_phone(phone)
		except Exception as ex:
			log(ex)