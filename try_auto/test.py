import requests as req
from lxml import etree
import random
import re


def sxs_encode(source):
    """
    密码加密函数
    :param source: 要加密的字符串
    :return: 返回加密后的字符串
    """
    encoded_str = list()
    for letter in list(source):
        encoded_str.append(str(ord(letter))[::-1])
    res_str = 'X'.join(encoded_str[::-1])
    return res_str


def login(phone_num, password):
    """
    首页登录函数，获取 cookie
    :param phone_num: 手机号码
    :param password: 登录密码
    :return: 返回登录后的 cookie
    """
    login_url = 'https://www.shixiseng.com/user/login'
    headers = {
        "Origin": "https://www.shixiseng.com",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/77.0.3865.90",
    }
    login_data = {
        "username": phone_num,
        "password": sxs_encode(password),
        "remember_login": 1,
    }
    login_res = req.post(login_url, headers=headers, data=login_data)
    user_cookie = login_res.cookies
    return user_cookie


def recommend_worklist(user_cookie, max_page=10):
    """
    获取推荐列表的接口
    :param user_cookie: 登录后得到的 cookie
    :param max_page: 最长获取的页面数量
    :return: 推荐中的工作列表 {work_name, work_link, work_salary, work_uid}
    """
    recommend_works_url = 'https://www.shixiseng.com/recommend/interns?p={}'
    headers = {
        "Origin": "https://www.shixiseng.com",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/77.0.3865.90",
    }
    page_count, work_list = 1, list()
    while True and page_count < max_page+1:
        res = req.get(recommend_works_url.format(page_count), headers=headers, cookies=user_cookie)
        works = etree.HTML(res.text).xpath('//div[@class="position-list fl"]/ul/li/div[1]/div[1]')
        for work in works:
            work_name = work.xpath('./a/text()')[0].strip()
            work_link = 'https://www.shixiseng.com' + work.xpath('./a/@href')[0].strip()
            work_salary = work.xpath('./span/text()')[0].strip()
            work_list.append({
                'work_name': work_name,
                'work_link': work_link,
                'work_salary': work_salary,
                'work_uid': re.findall('(?<=intern/).*?$', work_link)[0]
            })
        page_count += 1
        if res.status_code != 200:
            break
    return work_list


def add_to_favorite(user_cookie, work_list):
    """
    添加 work_list 中的工作到收藏的接口
    :param user_cookie: 登录后得到的 cookie
    :param work_list: 岗位列表
    :return: 无返回值
    """
    add_favo_url = 'https://www.shixiseng.com/trainee/favorite/add'
    headers = {
        "Origin": "https://www.shixiseng.com",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/77.0.3865.90",
    }
    job_data = {
        "ftype": "intern",
        "saveuuid": "",
    }
    for work in work_list:
        job_data['saveuuid'] = work['work_uid']
        add_res = req.post(add_favo_url, headers=headers, data=job_data, cookies=user_cookie).json()
        if add_res['code'] == 100:
            print(work['work_name'], '收藏成功')
        else:
            print(add_res['msg']['cont'])


def deliver_works(user_cookie, work_list):
    """
    投递职位列表 work_list 中的所有岗位的接口
    :param user_cookie: 登录后得到的 cookie
    :param work_list: 岗位列表
    :return: 无返回值
    """
    form_url = 'https://www.shixiseng.com/trainee/resume/deliver?intern_uuid={}&{}'
    deliver_url = 'https://www.shixiseng.com/trainee/resume/deliver'
    token_url = 'https://www.shixiseng.com/getsdtoken?{}'
    confirm_url = 'https://www.shixiseng.com/trainee/resume/deliver/confirm'
    headers = {
        "Origin": "https://www.shixiseng.com",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/77.0.3865.90",
    }
    form_data = {
        "inuuid": "",
        "guuid": "",
        "date": "3个月以内",
        "reportDate": "3个月内",
        "day": 1,
    }
    for work in work_list:
        work_uid = work['work_uid']
        select_form = req.get(form_url.format(work_uid, random.random()), headers=headers, cookies=user_cookie)
        # 这里得到两个 guid 值，第一个是在线简历，第二个是附件简历，其实不用这一步获取也可以，但可能每个人不相同，所以保险起见获取一下
        guids = etree.HTML(select_form.text).xpath('//ul[@id="resume_list_box"]/li/input/@data-guid')
        form_data['inuuid'] = work_uid
        form_data['guuid'] = guids[0]
        deliver_res = req.post(deliver_url, headers=headers, cookies=user_cookie, data=form_data).json()
        if deliver_res['code'] == 100:
            sdtoken_res = req.get(token_url.format(random.random()), headers=headers, cookies=user_cookie).text.strip()
            confirm_data = {
                "sdtoken": sdtoken_res,
                "score": deliver_res['msg']['score'],  # 在 deliver 的返回数据中
                "token": deliver_res['msg']['token'],  # 在 deliver 的返回数据中
                "inuuid": work_uid,
                "guuid": guids[0],
                "is_invite": "",
                "source": "",
                "activity": "",
                "pcm": ""
            }
            confirm_res = req.post(confirm_url, headers=headers, cookies=user_cookie, data=confirm_data).json()
            if confirm_res['code'] == 100:
                print(work['work_name'], 'deliver ok    ->', work['work_salary'])
            else:
                print(confirm_res['msg']['cont'])
        else:
            print(deliver_res['msg']['cont'])


cookie = login('15901593226', 'meiyuan304')  # 获取 cookie
job_list = recommend_worklist(cookie, 3)  # 获取 职位的列表
add_to_favorite(cookie, job_list)  # 收藏职位
deliver_works(cookie, job_list)  # 投递简历：使用的是 线上简历
