import serial
import threading
import time
import datetime
import queue
import json
import os
import pytz

class FarmproAT:
    def __init__(self) -> None:
        self._port = '/dev/ttyS2'
        self._baudrate = 115200
        self.IsAtConnect = False
        self.hSerial = None
        
        self.IsTCP = False
        self.tcp_ip="14.63.173.116"
        self.tcp_port="80"
        
        self.Data = {
            "FrameType": "F1",
            "GatewayEUI":"",
            "DateTime":"",
            "APN":"",
            "Network":"",
            "IMEI":"",
            "IMSI":"",
            "latitude":"",
            "longitude":""
        }
        
        self.sbuff = queue.Queue()
        
        self.recvEn = True
        self.recvTh = threading.Thread(target=self.RecvFunc, daemon=True)
        self.recvTh.start()
        
    def RecvFunc(self):
        while self.recvEn:
            if self.IsAtConnect:
                try:
                    rs = self.hSerial.readline()
                    if rs:
                        self.sbuff.put_nowait(rs.decode())
                        print('LTE> ' + rs.decode())
                except serial.SerialException:
                    self.hSerial.close()
                    self.IsAtConnect = False
                except:
                    pass
            else:
                while self.recvEn:
                    try:
                        self.hSerial = serial.Serial(port=self._port, baudrate=self._baudrate, timeout=1.0)
                    except serial.SerialException:
                        continue
                    else:
                        self.IsAtConnect = True
                        break
                    
    def SendCommand(self, command=''):
        if self.IsAtConnect and command != '':
            if self.hSerial.writable():
                self.hSerial.write(command.encode())
                
    def WaitRecv(self, filter='', timeout=1.0):
        words = None
        end_time = time.time() + timeout
        while time.time() < end_time:
            if not self.sbuff.empty():
                try:
                    line = self.sbuff.get_nowait()
                    words = str(line).replace(',', ' ').split()
                    
                    if filter == '':
                        if "OK" in line or "ERROR" in line:
                            break
                    elif filter in line:
                        if filter == 'QSPN' and words[0] == '+QSPN:':
                            # print(words[1][1:-1])
                            self.Data['Network'] = words[1][1:-1]
                        elif filter == 'CGDCONT' and len(words) > 3:
                            if words[1] == '1':
                                # print(words[3][1:-1])
                                self.Data['APN'] = words[3][1:-1]
                        # 임시 주석
                        # elif filter == 'CCLK' and "CCLK:" in words[0]:
                        #     ttstr = "\"20" + words[1][1:] + "," + words[2]
                        #     print(ttstr)
                        #     ltetime = datetime.datetime.strptime(ttstr, "\"%Y/%m/%d,%H:%M:%S+00\"")
                        #     print("LTE time : " + "/bin/date -s \"" + ltetime.strftime("%Y-%m-%d %H:%M:%S") + "\"")
                        #     os.system("/bin/date -s \"" + ltetime.strftime("%Y-%m-%d %H:%M:%S") + "\"")
                    elif filter == 'GSN' and len(words[0]) > 10:
                            self.Data['IMEI'] = words[0]
                    elif filter == 'CIMI' and len(words[0]) > 10:
                        self.Data['IMSI'] = words[0]
                except:
                    pass

    
    def OpenTCP(self):
        self.SendCommand("AT+QIACT=1\r\n")
        self.WaitRecv(timeout=3.0)
                
        self.SendCommand("AT+QIOPEN=1,0,\"TCP\",\""+self.tcp_ip+"\","+self.tcp_port+",0,1\r\n")
        self.WaitRecv(filter="QIOPEN", timeout=5.0)
        self.SendCommand("AT+QISTATE=1,0\r\n")
        self.WaitRecv(timeout=3.0)
        
        self.IsTCP = True
        
    def CloseTCP(self):
        self.SendCommand("AT+QICLOSE=0\r\n")
        self.WaitRecv(timeout=3.0)
        
        self.SendCommand("AT+QIDEACT=1\r\n")
        self.WaitRecv(timeout=3.0)
        
        self.IsTCP = False
                
    def SendTCP(self, Data=None):
        if not Data:
            return
        
        try:
            tempdata = json.dumps(Data)
        except:
            return
        
        myHeader = "PUT /receiveJson_20211223.php HTTP/1.1\nHost:"+self.tcp_ip+":"+self.tcp_port+"\nUser-Agent: python-requests/2.25.1\nAccept-Encoding: gzip, deflate\nAccept: */*\nConnection: keep-alive\nContent-Type: application/json\nContent-Length: %d\n\n" % (len(tempdata) + 6)
        restapi = myHeader + tempdata + "\r\n\r\n\r\n"
        
        if not self.IsTCP:
            self.OpenTCP()
        
        self.SendCommand("AT+QISEND=0,%d\r\n"%len(restapi))
        self.WaitRecv(filter=">")
        self.SendCommand(restapi)
        self.WaitRecv(filter="json", timeout=3.0)
        
    def UpdateInfo(self):
        self.SendCommand('\rAT+QSPN\r')
        rt = self.WaitRecv(filter="QSPN")
        
        self.SendCommand('\rAT+CGDCONT?\r')
        rt = self.WaitRecv(filter="CGDCONT")
        
        self.SendCommand('\rAT+GSN\r')
        rt = self.WaitRecv(filter="GSN")
        
        self.SendCommand('\rAT+CIMI\r')
        rt = self.WaitRecv(filter="CIMI")
        
        self.SendCommand('\rAT+CCLK?\r')
        rt = self.WaitRecv(filter="CCLK")
        
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
    app = FarmproAT()
    
    app.SendTCP()
        