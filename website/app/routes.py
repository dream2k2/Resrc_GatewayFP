from flask import render_template, request, redirect, url_for
from app import app
import json
import os

from app.apn_update import HeartBeat

@app.route("/", methods=["GET", "POST"])
def index_func():

    # html > javascript alert message
    message=None

    # html > form > POST request
    form_data = request.form

    # 메인 app 파일 상태 확인용
    f = open("/root/Gateway_swV2/autostart.sh", 'r')
    lines = f.readlines()
    text = lines[1]
    f.close()

    if text == "(sleep 180 && python3 /root/Gateway_swV2/app/gateway/main_basic.py /dev/ttyS1)\n":
        app_text = "Ethernet"
    elif text == "(sleep 180 && python3 /root/Gateway_swV2/app/gateway/main_at.py /dev/ttyS1)\n":
        app_text = "AT"
    else:
        app_text = "error"

    # 기존 json 파일 데이터 불러오기
    with open("/root/Gateway_swV2/GatewayConfig.json", 'r') as f:
        json_data = json.load(f)
    data_json = json_data

    # # APN, Network, IMEI, IMSI 불러오기
    # heart_beat = HeartBeat()
    # heart_beat.UpdateInfo()

    if request.method == "POST":

        if not form_data["GatewayID"] or not form_data["apn"] or not form_data["connect"] or not form_data["latitude"] or not form_data["longitude"]:
            message = "필수로 입력해주세요."
        else:
            GatewayID = form_data["GatewayID"]
            apn = form_data["apn"]
            connect = form_data["connect"]
            latitude = form_data["latitude"]
            longitude = form_data["longitude"]

            if form_data["button"] == "modify":

                # apn 설정하기 ex) connect.cxn
                # heart_beat.ApnUpdateInfo(apn) # 안써도 되는 함수
                os.system("o2lte apn %s" % apn)
        
                json_data['GatewayID'] = GatewayID
                json_data['Connect'] = "http://" + connect + "/receiveJson_20211223.php"
                json_data['latitude'] = latitude
                json_data['longitude'] = longitude

                # json 파일에 데이터 업데이트
                with open("/root/Gateway_swV2/GatewayConfig.json", 'w', encoding='utf-8') as modify_file:
                    json.dump(json_data, modify_file, indent="\t")

                message = "업데이트 되었습니다. 기기를 재부팅 하시길 바랍니다."

                # return render_template("index.html", title="Scanner Settings", data=data_json, heart_data=heart_beat, message=message)
                return render_template("index.html", title="Scanner Settings", data=data_json, app_set=app_text, message=message)
        
    # return render_template("index.html", title="Scanner Settings", data=data_json, heart_data=heart_beat, message=message)
    return render_template("index.html", title="Scanner Settings", data=data_json, app_set=app_text, message=message)


@app.route('/process', methods=['GET', 'POST']) 
def process(): 
    # APN, Network, IMEI, IMSI 불러오기
    heart_beat = HeartBeat()
    heart_beat.UpdateInfo()

    return render_template("process.html", title="Scanner Settings", heart_data=heart_beat)


@app.route("/setTel", methods=["POST"])
def set_tel_func():

    data = request.json

    set_tel = data['set_tel']
    other = data['other']

    try:
        # 통신사 강제 설정
        if "reset" == set_tel:
            os.system("python3 /root/Gateway_swV2/atcmd.py AT+COPS=0") # reset
        elif "skt" == set_tel:
            os.system("python3 /root/Gateway_swV2/atcmd.py AT+COPS=0") # reset
            os.system("python3 /root/Gateway_swV2/atcmd.py AT+COPS=1,2,\"45005\",7") # SKT
        elif "kt" == set_tel:
            os.system("python3 /root/Gateway_swV2/atcmd.py AT+COPS=0") # reset
            os.system("python3 /root/Gateway_swV2/atcmd.py AT+COPS=1,2,\"45008\",7") # KT
        elif "Other" == set_tel:
            os.system("python3 /root/Gateway_swV2/atcmd.py AT+COPS=0") # reset
            os.system('python3 /root/Gateway_swV2/atcmd.py ' + other) # 직접입력 # AT+COPS=1,2,"45008",7
        return "success"
    except:
        return "error"
    
@app.route("/setApp", methods=["POST"])
def set_app_func():

    data = request.json

    set_app = data['set_app']

    try:
        # 인터넷 연결 설정
        if "0" == set_app:
            f = open("/root/Gateway_swV2/autostart.sh", 'w')
            data = "#!/bin/bash \n(sleep 180 && python3 /root/Gateway_swV2/app/gateway/main_basic.py /dev/ttyS1)\n"
            f.write(data)
            f.close()

        elif "1" == set_app:
            f = open("/root/Gateway_swV2/autostart.sh", 'w')
            data = "#!/bin/bash \n(sleep 180 && python3 /root/Gateway_swV2/app/gateway/main_at.py /dev/ttyS1)\n"
            f.write(data)
            f.close()

        return "success"
    except:
        return "error"