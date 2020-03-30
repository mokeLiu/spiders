from Crypto.Cipher import AES
import requests
import urllib3
import shutil
import time
import os
import re


def ase_decode(decode_data, key, iv):
    cryptor = AES.new(key, AES.MODE_CBC, iv)
    plain_text = cryptor.decrypt(decode_data)
    return plain_text.rstrip(b'\0')


# 禁用安全警告
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
proxy = {
    'HTTP': '112.111.217.56:9999'
}
# 由于刚出现的 单点登录检测，所以先进行登录
smscode_url = 'https://www.mbadashi.com/api/web/v1/authorizations/smscode?mobile={}'
login_url = 'https://www.mbadashi.com/api/web/v1/authorizations/login'
mobile = input('请输入手机号：')
res = requests.get(smscode_url.format(mobile), proxies=proxy).json()
if res:
    if res['data'].strip() == '发送成功':
        auth_code = input('请输入验证码：')
        payload = '{{"authCode": "{}","loginWay": 2,"mobile": {}}}'.format(auth_code, mobile)
        res = requests.post(login_url, data=payload, proxies=proxy).json()
else:
    print(res)
# 构造请求的 cookie
t_stamp = int(time.time())
token = res['data']['token']
cookie = [
    'mba_adv=false',
    'Hm_lvt_ce194e4b1b78122b4d441f28bbc372eb={},{},{}'.format(t_stamp, t_stamp+50000, t_stamp+100000),
    'Hm_lpvt_ce194e4b1b78122b4d441f28bbc372eb={}'.format(t_stamp+100000),
    'JSESSIONID={}'.format(token),
    'token={}'.format(token),
]
cookie = '; '.join(cookie)
print(cookie)

# 对于已有 cookie 的情况
# cookie = '''mba_adv=false; Hm_lvt_ce194e4b1b78122b4d441f28bbc372eb=1585456318,1585506318,1585556318;
# Hm_lpvt_ce194e4b1b78122b4d441f28bbc372eb=1585556318; JSESSIONID=token-430588-0329123158-2-193117;
# token=token-430588-0329123158-2-193117'''

# 首页信息请求链接
index_url = 'https://www.mbadashi.com/api/web/v1/home/labels/2/list'
# 各个课程请求链接（总体信息、章节信息）
all_link = 'https://www.mbadashi.com/api/web/v1/course/{}/all'
chapter_link = 'https://www.mbadashi.com/api/web/v1/course/{}/chapters'
# 视频网址解析、请求、获取链接
# 其中的 fileId 可以从 chapter -> section -> videoInfo -> 得到
fir_req_url = 'https://www.mbadashi.com/api/web/v1/vod/playinfo?fileId={}&percent=10000'
# ↓ 得到：
# fileId: "5285890784529098820"
# sign: "0aeba51a6afbea546b8c23f9d91825e1"
# timeout: "5e5af3e9"
# us: "1pil4qbegj"
sec_req_url = 'https://playvideo.qcloud.com/getplayinfo/v2/1400177511/{}?sign={}&t={}&us={}'
# 组装方式：https://url + $fileId + ?sign= $sign + &t= $timeout + &us= $us
courses = requests.get(index_url, proxies=proxy).json()['data']
# courses共分为四类："近期直播"，"直播课堂"，"推荐课堂"，"免费系统课程"
headers = {
    "host": "www.mbadashi.com",
    "cookie": cookie,
    "user-Agent": "Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/77.0.3865.90",
}
if not os.path.exists('./MBA/'):
    os.mkdir('./MBA/')
for course in courses:
    if course['name'] == '免费系统课程':
        for item in course['cardList']:
            # 课程名称 -> 用于保存文件名
            class_name = item['name']
            print('正在获取课程：', class_name)
            # 创建课程文件夹
            class_path = './mba/'+class_name
            if not os.path.exists(class_path):
                os.mkdir(class_path)
            if not os.path.exists(class_path+'/video/'):
                os.mkdir(class_path+'/m3u8/')
                os.mkdir(class_path+'/video/')
            else:
                continue
            # 获取课程所需的配套电子教材链接 -> [dict]
            file_list = requests.get(all_link.format(item['relaId']), proxies=proxy).json()['data']['fileList']
            # 保存电子教材
            if len(file_list):
                os.mkdir(class_path+'/book/')
            for file in file_list:
                save_file = requests.get(file['url'], proxies=proxy).content
                save_name = file['name'].replace('\\', '-')
                with open(class_path+'/book/'+save_name+'.'+file['type'], 'wb') as f:
                    f.write(save_file)
            # 获取课程章节的链接
            chapter_url = chapter_link.format(item['relaId'])
            print(chapter_url)
            # 保存课程章节信息（整体信息）
            chapter_list = requests.get(chapter_url, proxies=proxy).json()['data']['chapterList']
            print(len(chapter_list))
            # 遍历每节课程的信息（从章节中抽取出用于获取视频的部分）
            for chapter in chapter_list:
                print(' '*3, '- 当前章节：', chapter['title'])
                for section in chapter['sectionList']:
                    # 获得当前视频的标题和文件ID
                    file_name = section['title'].strip('\t')
                    print(' '*8, '- 当前课程：', file_name)
                    file_id = section['videoInfo']['fileId']
                    file_time = section['videoInfo']['timeLongName'].strip('\t')
                    # 两次请求获得视频地址
                    # 注意：在第一次请求时，需要进行身份验证，需要添加Cookie
                    data = requests.get(fir_req_url.format(file_id), headers=headers, proxies=proxy).json()['data']
                    sec_req_url = sec_req_url.format(file_id, data['sign'], data['timeout'], data['us'])
                    play = requests.get(sec_req_url, proxies=proxy).json()
                    # 这里得到 转码md5 以及 视频链接地址 的列表（一个是标清，一个是高清）
                    # 还有一个masterPlayList应该是有播放记录的播放方式
                    # 取出来头一个（估计应该是高清）的链接和md5
                    # （master是master_playlist.m3u8）（高清是v.f230.m3u8）（标清是v.f220.m3u8）
                    video_url, video_req_head = None, None
                    for trans in play['videoInfo']['transcodeList']:
                        if trans['definition'] == 230:  # 获取高清的视频m3u8地址
                            video_url = trans['url']
                            video_req_head = re.findall('.*?drm/', video_url)[0]
                    # 请求m3u8链接
                    m3u8 = requests.get(video_url, proxies=proxy).content
                    m3u8_file_path = (class_path+'/m3u8/'+file_name+'_'+file_time+'.m3u8').replace(':', 'm')
                    with open(m3u8_file_path, 'wb') as f:
                        f.write(m3u8)
                    # 请求视频地址
                    video_key = None
                    with open(m3u8_file_path) as m3u8:
                        lines = m3u8.readlines()
                        tmp_ts_file = class_path + '/video/' + file_name+'.ts'
                        with open(tmp_ts_file, 'wb+') as ts:
                            for line in lines:
                                if not video_key and line.startswith('#EXT-X-KEY'):
                                    video_key_link = re.findall('https:.*?(?=",)', line)[0]
                                    video_key = requests.get(video_key_link, proxies=proxy).content
                                if line.startswith('v.f'):
                                    video_link = video_req_head+line.strip('\n')
                                    res = requests.get(video_link, stream=True, verify=False, proxies=proxy)
                                    ts.write(ase_decode(res.content, video_key, b'0'*16))
                        mp4_file = class_path+'/video/'+file_name+file_time+'s.mp4'
                        shutil.move(tmp_ts_file, mp4_file.replace(':', 'm'))
                    print(' '*8, '- 视频保存完成：')
