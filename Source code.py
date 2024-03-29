import time
from PIL import Image
from PIL import ImageDraw
from PIL import ImageFont
import Adafruit_SSD1306
import RPi.GPIO as GPIO
import threading
import socket
import struct
import re
import os
import sys
import timeit
from subprocess import call
from enum import Enum, unique
from traceback import print_exc
from aiy.board import Board
from aiy.voice.audio import AudioFormat, play_wav, record_file, Recorder
import Adafruit_GPIO.SPI as SPI

def display_text(text, *args):
    if len(args) < 2:
        FONT_SIZE = 15
    elif len(args) == 2:
        FONT_SIZE = 10
    else:
        FONT_SIZE = 8
    disp = Adafruit_SSD1306.SSD1306_128_32(rst = 0)

    width = disp.width
    height = disp.height

    # 1 bit pixel
    image = Image.new('1', (width, height))
    draw = ImageDraw.Draw(image)
    font = ImageFont.truetype("./ARIALUNI.TTF", FONT_SIZE)
    try:
    #print('Press ^C to terminate')
       # while True:
        draw.rectangle((0, 0, width, height), outline = 0, fill = 0)
        draw.text((0, 0), text, font = font, fill = 255)
        if len(args) > 0:
            for i, item in enumerate(args):
                draw.text((0, (i + 1) * FONT_SIZE-1), item, font = font, fill = 255)
        disp.image(image)
        disp.display()
        time.sleep(0.2)
    except KeyboardInterrupt:
        print('terminated')


 
#GPIO Mode (BOARD / BCM)
GPIO.setmode(GPIO.BCM)
 
#set GPIO Pins
GPIO_TRIGGER = 25 #23->25
GPIO_ECHO = 24
 
#set GPIO direction (IN / OUT)
GPIO.setup(GPIO_TRIGGER, GPIO.OUT)
GPIO.setup(GPIO_ECHO, GPIO.IN)
 
def distance():
    # set Trigger to HIGH
    GPIO.output(GPIO_TRIGGER, True)
 
    # set Trigger after 0.01ms to LOW
    time.sleep(0.00001)
    GPIO.output(GPIO_TRIGGER, False)
 
    StartTime = time.time()
    StopTime = time.time()
 
    # save StartTime
    while GPIO.input(GPIO_ECHO) == 0:
        StartTime = time.time()
 
    # save time of arrival
    while GPIO.input(GPIO_ECHO) == 1:
        StopTime = time.time()
 
    # time difference between start and arrival
    TimeElapsed = StopTime - StartTime
    # multiply with the sonic speed (34300 cm/s)
    # and divide by 2, because there and back
    distance = (TimeElapsed * 34300) / 2
 
    return distance


def motor(): 
    GPIO.setmode(GPIO.BCM)
 
    STEPS_PER_REVOLUTION = 32 * 64
    SEQUENCE = [[1, 0, 0, 0], 
                [1, 1, 0, 0],
                [0, 1, 1, 0],
                [0, 0, 1, 1]]


    STEPPER_PINS = [17,18,27,22]
    for pin in STEPPER_PINS:
        GPIO.setup(pin,GPIO.OUT)
        GPIO.output(pin, GPIO.LOW)
 
    SEQUENCE_COUNT = len(SEQUENCE)
    PINS_COUNT = len(STEPPER_PINS)
 
    sequence_index = 0
    direction = 1
    steps = 0
 
    if len(sys.argv)>1:
        wait_time = int(sys.argv[1])/float(1000)
    else:
        wait_time = 10/float(1000)
 
    n=0
    while(n<350):
        n=n+1
        for pin in range(0, PINS_COUNT):
            GPIO.output(STEPPER_PINS[pin], SEQUENCE[sequence_index][pin])
        steps += direction
        if steps >= STEPS_PER_REVOLUTION:
            direction = -1
        elif steps < 0:
            direction = 1
        sequence_index += direction
        sequence_index %= SEQUENCE_COUNT
        #print('index={}, direction={}'.format(sequence_index, direction))
        time.sleep(wait_time)

Lab = AudioFormat(sample_rate_hz=16000, num_channels=1, bytes_per_sample=2)

#taiwanese_tts.py
def askForService_res(token, data, model="F06"):
    # HOST, PORT 記得修改
    global HOST_res
    global PORT_res
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    received = ""
    try:
        sock.connect((HOST_res, PORT_res))
        msg = bytes(token+"@@@"+data+"@@@"+model, "utf-8")
        msg = struct.pack(">I", len(msg)) + msg
        sock.sendall(msg)
        
        with open('output.wav','wb') as f:
            while True:
                # print("True, wait for 15sec")
                # time.sleep(15)
                
                l = sock.recv(8192)
                # print('Received')
                if not l: break
                f.write(l)
        play_wav("output.wav")
        print("File received complete")
    finally:
        sock.close()
    return "OK"
### Don't touch

def process_res(token,data):
    result = askForService_res(token,data)
    return result

global HOST_res
global PORT_res
######### 注意：以下數字，10008為原版，10010套用實驗室變調版，10012則是接受中文輸入，即多套一個中文轉台羅
### ***10008以及10010接受台羅，10012接受中文
HOST_res, PORT_res = "140.116.245.146", 10008

def record():
	with Board() as board:
		print('請按下按鈕開始錄音.')
		board.button.wait_for_press()
		done = threading.Event()
		board.button.when_pressed = done.set
		
		def wait():
			start = time.monotonic()
			while not done.is_set():
				duration = time.monotonic() - start
				print('錄音中: %.02f 秒 [按下按鈕停止錄音]' % duration)
				time.sleep(0.5)
		record_file(Lab, filename='recording.wav', wait=wait, filetype='wav')
def main():
#	while True:
		record()
		print("播放音檔...")
		play_wav("recording.wav")


def askForService(token, data):
    # HOST, PORT 記得修改
    HOST = "140.116.245.149"
    PORT = 2802
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    model = "Minnan"
    try:
        sock.connect((HOST, PORT))
        msg = bytes(token + "@@@", "utf-8") + struct.pack("8s",bytes(model, encoding="utf8")) + b"P" + data
        msg = struct.pack(">I", len(msg)) + msg  # msglen
        sock.sendall(msg)
        received = str(sock.recv(1024), "utf-8")
    finally:
        sock.close()
    return received

def process(token, data):
    # 可在此做預處理
    # 送出
    result = askForService(token, data)
    # 可在此做後處理
    return result

if __name__ == "__main__":
    '''
    超音波函式+馬達函式
    如果距離夠近，改變表情並結束函式
    1.回覆：你好我是杯麵請問需要幫忙嗎
      process(token,"")
    '''
    token = "eyJhbGciOiJSUzUxMiIsInR5cCI6IkpXVCJ9.eyJleHAiOjE2NDkxNjUxNTgsImlhdCI6MTYzMzYxMzE1OCwic3ViIjoiIiwiYXVkIjoid21ta3MuY3NpZS5lZHUudHciLCJpc3MiOiJKV1QiLCJ1c2VyX2lkIjoiMjkwIiwibmJmIjoxNjMzNjEzMTU4LCJ2ZXIiOjAuMSwic2VydmljZV9pZCI6IjMiLCJpZCI6Mzk3LCJzY29wZXMiOiIwIn0.V5H83lIze4RNTf6AGZUf34e6XVtlnVlpUHBLbdJUhL4KK4KPUWDQ3jcallP676OxRVZFn9ExcfxVPhnIZWyVIoxJr09Nothe16_gtLVQVxFNWtbPm5qCaWEEQZeY9vcvQwkI9wMzf_z-xWi0v7bkkqhaAK59qtQZDgYF7r5ztyM" # 需要申請
    dist=1000
    while(dist>40):
        dist=distance()
        print("d=%.1f" % dist)
        dist=round(dist,1)
        display_text("distance:"+str(dist))
        time.sleep(1)

    answer=""
    while True:
        process_res(token,"u7 siann2 mih beh tau3 sann kang7 bo5")
        motor()
        main()
        file_name = "recording.wav"
        file = open(r"./{}".format(file_name), 'rb')
        data = file.read()
        total_time = 0
        count = 0.0
        #process_res(token,"u7 siann2 mih beh tau3 sann kang7 bo5")
        result=process(token, data)
        print(result)
        i=0
        answer=""
        for c in result:
            # print(c)
            if(i>=6):
                if(('\u4e00'<=c and c<='\u9fa5') or c.isspace()):
                    # print("c=",c)
                    if(not c.isspace()):
                        answer=answer+c
                        #  print("answer=",answer)
                else:
                    # print("break")
                    break
            i+=1
        if("多謝" in answer):
            process_res(token,"ho2 hi bang7 li u7 huann hi2 e5 tsit8 kang")
            break

        
        #食
        #Q：台南有什麼好吃的 A：豆腐冰最好吃
        if(("臺南" in answer or "台南" in answer) and "有" in answer and "啥物" in answer):
            process_res(token,"tau7 hu7 ping siong7 ho2 tsiah8 ")                    
        #Q：晚餐要吃什麼 A：吃什麼都好不要吃 太多就好
        elif("暗頓" in answer):
            process_res(token,"tsiah8 siann2 mih long2 e7 sai2 mai3 tsiah8 siunn tsue")
        #Q：宵夜吃炸雞好嗎 A：想變成大箍呆
        elif("宵夜" in answer or "炸雞" in answer):
            process_res(token,"siunn7 beh pian3 sing5 yua7 khoo tai nih")
        #Q：吃什麼不變大胖子 A：什麼都不要吃
        elif("大箍呆" in answer):
            process_res(token,"siann2 mih long2 mai3 tsiah8")
        #Q：成功大學肉圓好吃嗎 A：你可以試試
        elif("成功" in answer and "大學" in answer):
            process_res(token,"li e7 tang3 tshi3 khuann3 mai7")
        #Q：一天要喝多少水 A：2公升
        elif("一工" in answer and "水" in answer):
            process_res(token,"nng2 kong sing")
        #Q：我最愛什麼飲料 A：我怎麼知道
        elif("上愛" in answer or "涼水" in answer):
            process_res(token,"gua2 na2 e7 tsai iann2")
        #Q：夜市有什麼好吃的 A：臭豆腐和蚵仔煎
        elif("夜市" in answer ):
            process_res(token,"tshau3 tau7 hu7 koh u7 o5 a2 tsian ")
        #Q：可以吃肉不吃菜好嗎 A：如果你想便秘的話
        elif(("食" in answer and "肉" in answer) or "食菜" in answer):
            process_res(token,"na7 si7 li siunn7 beh pi3 kiat")
        #Q：替我買早餐好嗎 A：你沒有腳嗎
        elif("早頓" in answer or "替" in answer):
            process_res(token,"li si7 bo5 kha nih")
        #樂
        #Q：你喜歡看什麼動畫 A：熊熊遇見你
        elif("動畫" in answer or "佮" in answer):
            process_res(token,"him5 him5 tu2 tioh8 li")
        #Q：有推薦的電影嗎 A：黑寡婦
        elif("電影" in answer and "推薦" in answer):
            process_res(token,"oo kua2 hu7")
        #Q：你想和我一起去看電影嗎 A：你請我我就去
        elif("看" in answer and "電影" in answer):
            process_res(token,"li tshiann2 gua2 gua2 tioh8 khi3")
        #Q：台南有哪裡好玩的 A:安平老街
        elif("好耍" in answer):
            process_res(token,"an ping5 lau ke")
        #Q：要不要去唱歌 A：我不想聽你唱歌
        elif("唱歌" in answer):
            process_res(token,"gua2 bo5 siunn7 beh thiann li tshiunn3 kua")
        #Q：台灣有什麼名產 A：鳳梨酥和珍珠奶茶
        elif("名產" in answer or "台灣" in answer or "臺灣" in answer):
            process_res(token,"ong5 lai5 soo koh u7 hun2 inn5 ling te5")
        #Q：今天天氣可以打籃球如何 A：今天太冷了比較適合睡覺
        elif("天氣" in answer or "籃球" in answer):
            process_res(token,"kin a2 jit8 ling2 ki ki khah sik hap8 khi3 khun3")
        #Q：你的興趣是什麼 A：吐槽你
        elif("興趣" in answer):
            process_res(token,"thuh tshau3 li")
        #Q：有什麼有名的電視劇可以看 A：夜市人生有夠讚
        elif("有名" in answer or "電視" in answer):
            process_res(token,"ia7 tshi7 lin5 sing u7 kau3 tsan2")
        #Q：附近哪裡有百貨公司 A：火車站對面有一間
        elif("百貨公司" in answer or "附近" in answer):
            process_res(token,"hue2 tshia tsam7 tui3 bin7 u7 it kan")
        #醫療
        #Q：感冒用斯斯好嗎 A：他不參類固醇、不傷身體
        elif("感冒" in answer):
            process_res(token,"i be7 tsham bi2 kok sian tan bi2 siunn sin the2")
        #Q：你怎麼沒感覺 A：我血液循環不好
        elif("感覺" in answer):
            process_res(token,"gua2 hueh ik8 sun5 huan5 m7 ho2")
        #Q：要吃什麼比較健康 A：青菜和水果
        elif("健康" in answer):
            process_res(token,"tsui2 ko2 koh u7 tshenn tshai3 ")
        #Q：洗手的口訣是什麼 A：溼、搓、沖、捧、擦
        elif("洗手" in answer):
            process_res(token,"tam5 so tshiong phong2 tshit")
        #Q：燙傷要怎麼處理 A：沖、脫、泡、蓋、送
        elif("燙傷" in answer or "處理" in answer):
            process_res(token,"tshiang5 thng3 phau3 khap sang3")
        #Q：注射後發燒怎麼辦 A：吃退燒藥多休息
        elif("發燒" in answer or "注射" in answer):
            process_res(token,"tsiah8 the3 sio ioh8 au7 khi3 hioh khun3")
        #Q：瘀青怎麼辦 A：先冰敷再熱敷
        elif("烏" in answer):
            process_res(token,"sing u3 ping koh u3 sio")
        #Q：牙齒在搖怎麼辦 A：去找牙醫給你拔掉
        elif("喙齒" in answer):
            process_res(token,"khi3 tshue7 khi2 kho i sing hoo7 li puih8 tiau7")
        #Q：讀書就不舒服怎麼辦　A：那就不要讀去休息
        elif("讀冊" in answer):
            process_res(token,"mai3 thak8 kuann2 kin2 hioh khun3")
        #Q：眼睛痛怎麼辦　A：看遠方或是點眼藥水
        elif("目睭" in answer or "疼" in answer):
            process_res(token,"khuann3 uan2 hong iah8 si7 tiam2 bak8 ioh8 tsui2")
    