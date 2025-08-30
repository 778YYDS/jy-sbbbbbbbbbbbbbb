import requests
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime
import sys
import time
import json
import warnings
import random
from requests.packages.urllib3.exceptions import InsecureRequestWarning
import base64
import ddddocr
import base64
from fastapi import FastAPI, HTTPException
from typing import Dict
from pydantic import BaseModel
import uvicorn
import threading
import time
import requests
import os

# 忽略 InsecureRequestWarning 警告
warnings.simplefilter('ignore', InsecureRequestWarning)
# 邮件配置

sender_email_fixed = '1878966904@qq.com'
auth_code = 'uymwbrfpihauejgc'
smtp_server = 'smtp.qq.com'
smtp_port = 465

# 第一个脚本的邮件主题和内容
subject_1 = '{time_str} {city} {km_code} 登陆成功'
body_template_1 = '登陆卡密: {km_code}\n登陆IP: {ip}\n登陆城市: {city}'

# 第二个脚本的邮件主题和内容
subject_2 = '接单成功: 订单名称: {order_name}'
body_template_2 = '接单响应: {response}\n\n本次抢单次数: {order_count}'

# API 端点 URL

# 登录接口
login_url = 'https://kf203.aulod.com/api/wxapp/member_play/pass_login'
# 获取订单列表1
find_order_list_url = 'https://kf203.aulod.com/api/wxapp/play_order/find_order_list'
# 抢单接口
receive_order_url = 'https://kf203.aulod.com/api/wxapp/play_order/receive_order'
# 获取订单列表2
is_new_order_url = 'https://kf203.aulod.com/api/wxapp/play_order/is_new_order'
# verify接口
verify_url = 'https://kf203.aulod.com/api/wxapp/play_order/verify'
# OCR识别api接口
# url_ocr = "http://158.178.239.154:8000/ocr"
# 图片路径
# image_path = km_code + ".jpg"

# 定义 openid 列表
openid_list = [
    "o2xb17106d50ec63e51481772ed58b794a5",
    "o2x639cfafa7ea0ee647f03aa38d1a53fc7",
    "o2x9d8b91918701651c5830d831426d6db7",
    "o2x107d74718679b5daa66db1e25a40a592",
    "o2x49dbf4c5236f0f0e563057a07a1bfcdd",
    "o2x4ca822146d533c8b7581221c7543e89b",
    "o2x639cfafa7ea0ee647f03aa38d1a53fc7",
    "o2x722360a9cbcea55aa17062921a58d08a",
    "o2x7b0737fdfb31223089c5bb30892d1f3a",
    "o2x4f56ffdcb8d3adb3ffcb6dce94b84d68",
    "o2xb12316bf8bc9017167afc016e94d97ef",
    "o2xe62fbbd18e092b9726cb2c7130563703",
    "o2x0e8673a9a12d7175d9b0ca921105c632",
    "o2xd3cbb827bef2fcd4112275551a99daf6",
    "o2x1ea52d52b0f3c2332b1d655ef755ed0b",
    "o2x0e8ad73a692c86a5ac0288c34dae7623",
    "o2x393a9a3082db7a9911e26e3b365446f4",
    "o2x7b059d86f90497f2cd687281b2171f1a",
    "o2x8eb45626bb53dc7196087ef4a58920bb",
    "o2x64d5e9eae017bad75e46b37f2bfc50d7",
    "o2x037fbde1f3e3e29fa7b8781495dc2e15",
]

ocr_headers = {
    'Connection':
    'Keep-Alive',
    'User-Agent':
    'Mozilla/4.0 (compatible; MSIE 8.0; Windows NT 5.1; Trident/4.0)',
}

# # 初始化请求头信息
# headers = {
#     'openid': 'o2xb17106d50ec63e51481772ed58b794a5',
#     'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36 NetType/WIFI MicroMessenger/7.0.20.1781(0x6700143B) WindowsWechat(0x63090b19) XWEB/11177 Flue',
#     'Content-Type': 'application/json;charset=UTF-8',
#     'Accept': '*/*',
#     'Origin': 'https://kf203.aulod.com',
#     'Referer': 'https://kf203.aulod.com/h5/',
#     'Accept-Encoding': 'gzip, deflate, br',
#     'Accept-Language': 'zh-CN,zh;q=0.9',
# }


def resource_path(relative_path):
    """获取资源的绝对路径，适用于开发环境和打包后的环境"""
    if hasattr(sys, '_MEIPASS'):
        # PyInstaller 打包环境
        base_path = sys._MEIPASS
    else:
        # 基于脚本所在的目录，而不是当前工作目录
        base_path = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(base_path, relative_path)


# 初始化 ddddocr
ocr = ddddocr.DdddOcr(det=False,
                      ocr=False,
                      show_ad=False,
                      import_onnx_path=resource_path("models/95%.onnx"),
                      charsets_path=resource_path("models/charsets.json"))


# 定义请求模型
class ImageRequest(BaseModel):
    image: str


def perform_ocr(base64_image: str) -> str:
    """
    接收base64编码的图片字符串进行OCR识别
    """
    try:
        # 处理可能包含的base64前缀
        if "base64," in base64_image:
            # 如果包含前缀，去除前缀
            base64_image = base64_image.split("base64,")[1]

        # 解码base64图片
        try:
            image_bytes = base64.b64decode(base64_image)
        except Exception:
            raise HTTPException(status_code=400,
                                detail="Invalid base64 string")

        result = ocr.classification(image_bytes)
        return result
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


def create_app() -> FastAPI:
    """
    创建并配置 FastAPI 应用
    """
    app = FastAPI(title="OCR API")

    @app.post("/ocr/", response_model=Dict[str, str])
    async def read_image(request: ImageRequest):
        result = perform_ocr(request.image)
        return {"result": result}

    return app


def start_server(host: str = "0.0.0.0", port: int = 8000):
    """
    启动 FastAPI 服务器
    """
    app = create_app()
    uvicorn.run(app, host=host, port=port)


def run_server_in_thread(host: str = "0.0.0.0", port: int = 8000):
    """
    在后台线程中启动 FastAPI 服务器
    """
    thread = threading.Thread(target=start_server, args=(host, port))
    thread.daemon = True  # 设置为守护线程，这样主程序退出时会自动结束
    thread.start()

    # 等待服务器启动
    server_url = f"http://{host}:{port}/docs"
    max_retries = 10
    for _ in range(max_retries):
        try:
            requests.get(server_url)
            print(f"OCR server is running at http://{host}:{port}")
            return True
        except requests.exceptions.ConnectionError:
            time.sleep(0.5)

    # print("Failed to start OCR server")
    return False


def ocr_request(image_base64: str,
                host: str = "0.0.0.0",
                port: int = 8000) -> str:
    """
    发送OCR请求到服务器
    """
    url = f"http://{host}:{port}/ocr/"
    response = requests.post(url, json={"image": image_base64})
    if response.status_code == 200:
        return response.json()["result"]
    else:
        raise Exception(f"OCR request failed: {response.text}")


# 请求体 获取订单信息
find_order_data = {'is_receive': True, 'page': 1}
# 请求体 无用上传
is_new_order_data = {}
# 初始化抢单次数计数器
order_count = 0


def upload_image(file_base64, url_ocr="http://localhost:8000/ocr/"):
    try:
        # 将base64字符串包装在字典中，键名为"image"
        data = {"image": file_base64}
        response = requests.post(url_ocr, json=data)
        response.raise_for_status()

        # 获取JSON响应
        result = response.json()
        return result["result"]  # API返回的格式是 {"result": "识别结果"}

    except requests.exceptions.RequestException as e:
        print(f"请求错误: {e}")
        return None
    except Exception as e:
        print(f"处理错误: {e}")
        return None


def send_email_user(subject, body, recipient_email):
    """发送邮件到用户输入的收件人邮箱"""
    msg = MIMEMultipart()
    msg['From'] = sender_email_fixed
    msg['To'] = recipient_email
    msg['Subject'] = subject
    msg.attach(MIMEText(body, 'plain'))
    try:
        with smtplib.SMTP_SSL(smtp_server, smtp_port) as server:
            server.login(sender_email_fixed, auth_code)
            server.sendmail(sender_email_fixed, recipient_email,
                            msg.as_string())
            print('邮件发送成功')

            print('窗口将在10s后关闭')
            time.sleep(10)
    except Exception as e:
        print(f'邮件发送失败: {e}')


last_openid = None  # 记录上一次的 openid


def fetch_data(recipient_email, user_area, user_amount, wait_time):
    global order_count
    global last_openid
    random.seed()
    # 保证和上一次不一样
    available = [oid for oid in openid_list if oid != last_openid]
    current_openid = random.choice(available)
    last_openid = current_openid

    headers = {
        'openid': current_openid,
        'User-Agent': 'Mozilla/5.0 ...',
        'Content-Type': 'application/json;charset=UTF-8',
        'Accept': '*/*',
        'Origin': 'https://kf203.aulod.com',
        'Referer': 'https://kf203.aulod.com/h5/',
        'Accept-Encoding': 'gzip, deflate, br',
        'Accept-Language': 'zh-CN,zh;q=0.9',
    }
    print(f"本次使用的 openid: {current_openid}")
    try:
        # print('第'+ str(order_count) + '次')
        # 获取订单列表数据
        time.sleep(0)

        response_is_new_order = requests.post(
            is_new_order_url,
            headers=headers,
            data=json.dumps(is_new_order_data),
            verify=False)
        response = requests.post(find_order_list_url,
                                 headers=headers,
                                 data=json.dumps(find_order_data),
                                 verify=False)

        response_is_new_order.raise_for_status()
        response.raise_for_status()
        data = response.json()

        # 检查数据并随机选择一条匹配的订单发送接单请求
        if data.get('code') == 1 and data.get('data', {}).get('total', 0) > 0:
            orders = data['data']['data']
            matching_orders = [
                order for order in orders if (order['send1'] == '暗区突围')
            ]

            if matching_orders:
                # 使用 max() 函数，根据订单金额选择最大值
                selected_order = max(matching_orders,
                                     key=lambda x: float(x.get('amount', 0)))

                # 获取验证码、、、、、、、、、、、、、、、、、、、、、、
                verify_response = requests.post(
                    verify_url,
                    headers=headers,
                    data=json.dumps(is_new_order_data),
                    verify=False)
                verify_response.raise_for_status()
                data_verify_response = verify_response.json()
                # 提取base64编码的图片数据
                image_base64 = data_verify_response["data"]["image"]
                # 如果你只想要去掉 `data:image/png;base64,` 部分并获取纯粹的 base64 字符串
                image_base64_pure = image_base64.split(",")[1]

                # 调用上传函数
                result = upload_image(file_base64=image_base64_pure)
                # print(result)
                warn_illegality = data_verify_response.get('data', {}).get(
                    'warn_illegality', None)
                post_data = {
                    'id': selected_order['id'],
                    "receive_type": 2,
                    "only_code_id": warn_illegality,
                    "check_code": result
                }

                # print(f"等待 {wait_time:.2f} 秒后接单 {selected_order['sku_name']}...")
                time.sleep(wait_time)

                receive_response = requests.post(receive_order_url,
                                                 headers=headers,
                                                 data=json.dumps(post_data),
                                                 verify=False)
                receive_response.raise_for_status()
                response_data = receive_response.json()
                print('接单响应:', response_data)
                print(
                    f"成功接单 {selected_order['sku_name']}，等待了 {wait_time:.2f} 秒。"
                )

                # 获取 msg 的值
                msg_value = response_data['msg']
                # 判断 msg的值
                if msg_value == "接单成功":

                    # 发送邮件并包含接单响应及抢单次数
                    send_email_user(
                        subject_2.format(
                            order_name=selected_order['sku_name']),
                        body_template_2.format(response=response_data,
                                               order_count=order_count),
                        recipient_email)

                    return True

                else:
                    # print(f"接单失败，msg_value: {msg_value}，重新尝试...")
                    # 在接单失败时重新执行前面的代码
                    return True

    except requests.RequestException as e:
        print('请求失败:', e)
    return False


# 主程序
if __name__ == "__main__":
    run_server_in_thread()  # 启动 OCR 服务器
    # time.sleep(2)  # 确保服务器启动
    # 示例参数，需根据实际需求设置
    recipient_email = '1878966904@qq.com'
    user_area = ''
    user_amount = '10'
    wait_time = '1'
    wait_time = float(wait_time)
    while True:
        if fetch_data(recipient_email, user_area, user_amount, wait_time):
            # print("抢单成功")
            order_count += 1

    print("抢单失败，2秒后重试...")
    time.sleep(2)  # 失败后等待2秒再重试
