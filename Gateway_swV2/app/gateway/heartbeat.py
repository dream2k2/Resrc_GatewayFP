import serial
import threading
import time
import datetime
import queue
import json
import os
import pytz
import requests
import random

class HeartBeat():
    def __init__(self) -> None:
        self.Data = {
            "FrameType": "F1",
            "GatewayEUI":"",
            "DateTime":"",
            "APN":"",
            "Network":"",
            "IMEI":"",
            "IMSI":"",
            "latitude":"",
            "longitude":"",
            # "GavigeData0":"012345689012345689012345689",
            # "GavigeData1":"012345689012345689012345689",
            # "GavigeData2":"012345689012345689012345689",
            # "GavigeData3":"012345689012345689012345689",
            # "GavigeData4":"012345689012345689012345689"
        }
        
        self.mySerial = serial.Serial('/dev/ttyS2', 115200, timeout=0.5)
        self.sbuff = queue.Queue(100)
        
        self.recvEn = True
        self.recvTh = threading.Thread(target=self.RecvFunc, daemon=True)
        
        self.recvTh.start()
    
    def RecvFunc(self):
        while self.recvEn:
            try:
                rs = self.mySerial.readline()
                self.sbuff.put_nowait(rs.decode())
                print('LTE> ' + rs.decode())
            except:
                pass
            
    def Close(self):
        self.recvEn = False
        self.mySerial.cancel_read()
        
        self.recvTh.join()
            
    def RecvPars(self, cmd):
        while not self.sbuff.empty():
            try:
                if cmd == 'CCLK':
                    tstr = str(self.sbuff.get_nowait()).split()
                else:
                    tstr = str(self.sbuff.get_nowait()).replace(',', ' ').split()
            except:
                continue
            
            if tstr:
                if cmd == 'QSPN' and tstr[0] == '+QSPN:':
                    # print(tstr[1][1:-1])
                    self.Data['Network'] = tstr[1][1:-1]
                elif cmd == 'CGDCONT' and len(tstr) > 3:
                    if tstr[1] == '1':
                        # print(tstr[3][1:-1])
                        self.Data['APN'] = tstr[3][1:-1]
                elif cmd == 'GSN' and len(tstr[0]) > 10:
                    self.Data['IMEI'] = tstr[0]
                elif cmd == 'CIMI' and len(tstr[0]) > 10:
                    self.Data['IMSI'] = tstr[0]
                # 임시 주석 20240213 -> 해제 20240216
                elif cmd == 'CCLK' and "CCLK:" in tstr[0]:
                    ttstr = "\"20" + tstr[1][1:]
                    print(ttstr)
                    ltetime = datetime.datetime.strptime(ttstr, "\"%Y/%m/%d,%H:%M:%S+00\"")
                    print("LTE time : " + "/bin/date -s \"" + ltetime.strftime("%Y-%m-%d %H:%M:%S") + "\"")
                    os.system("/bin/date -s \"" + ltetime.strftime("%Y-%m-%d %H:%M:%S") + "\"")
            
    def UpdateInfo(self):
        self.mySerial.write('\rAT+QSPN\r'.encode())
        time.sleep(0.5)
        self.RecvPars('QSPN')
        
        self.mySerial.write('\rAT+CGDCONT?\r'.encode())
        time.sleep(0.5)
        self.RecvPars('CGDCONT')
        
        self.mySerial.write('\rAT+GSN\r'.encode())
        time.sleep(0.5)
        self.RecvPars('GSN')
        
        self.mySerial.write('\rAT+CIMI\r'.encode())
        time.sleep(0.5)
        self.RecvPars('CIMI')
        
        self.mySerial.write('\rAT+CCLK?\r'.encode()) # 임시 주석 20240213 -> 해제 20240216
        time.sleep(0.5) # 임시 주석 20240213 -> 해제 20240216
        self.RecvPars('CCLK') # 임시 주석 20240213 -> 해제 20240216
        
        # self.recvEn = False
        # self.mySerial.cancel_read()
        self.Close()
        
        korea = pytz.timezone('Asia/Seoul')
        utc_dt = datetime.datetime.utcnow()
        utc_dt = pytz.utc.localize(utc_dt)
        korea_dt = korea.normalize(utc_dt.astimezone(korea))
        self.Data['DateTime'] = korea_dt.strftime('%Y-%m-%d %H:%M:%S')
        
        file = os.path.join(os.path.dirname(__file__), "../../GatewayConfig.json")
        with open(file) as f:
            self.Data['GatewayEUI'] = (json.load(f))["GatewayID"]

# Script entry point.
if __name__ == "__main__":
    file = os.path.join(os.path.dirname(__file__), "../../GatewayConfig.json")
    with open(file) as f:
        configjson = json.load(f)
        
    try:
        stream = os.popen('ubus call gps info')
        output = json.loads(stream.read())
        if not "latitude" in output:
            gps = json.dumps(configjson)
        else:
            configjson["latitude"] = output["latitude"]
            configjson["longitude"] = output["longitude"]
            
            gps = json.dumps(output)
    except:
        gps = json.dumps({
                "age": 0,
                "latitude": 0,
                "longitude": 0,
                "elevation": "20.9",
                "course": "7.5",
                "speed": "0.0"
            })
        
    gpsjson = json.loads(gps)
    
    app = HeartBeat()
    
    app.UpdateInfo()
    
    print(app.Data)
    
    try:
        if gpsjson["latitude"] and gpsjson["longitude"]:
            app.Data['latitude'] = gpsjson["latitude"]
            app.Data['longitude'] = gpsjson["longitude"]
    except:
        pass
    
    print(json.dumps(app.Data, indent=4))
    
    # try:
    #     delay = random.randint(0, 600) / 10
    #     print("Delay : " + str(delay))
    #     time.sleep(delay)
        
    #     headers = {'Content-Type': 'application/json; charset=utf-8'}
    #     # url = ReadServerInfo()
    #     url = configjson["Connect"]
    #     response = requests.put(url, headers=headers, data=json.dumps(app.Data, indent=4, sort_keys=True))
    # finally:
    #     if response:
    #         print('response:', response.status_code)
    #     else:
    #         print('Response value Error!')
            
    app.Close()