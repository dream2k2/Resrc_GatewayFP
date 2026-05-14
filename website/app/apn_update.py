import serial
import threading
import time
import datetime
import queue
import pytz

class HeartBeat():
    def __init__(self) -> None:
        self.Data = {
            "FrameType": "F1",
            "DateTime":"",
            "APN":"",
            "Network":"",
            "IMEI":"",
            "IMSI":"",
        }
        
        self.sbuff = queue.Queue()
        
        self.mySerial = serial.Serial('/dev/ttyS2', 115200, timeout=1.0)

        self.recvEn = True
        self.recvTh = threading.Thread(target=self.RecvFunc, daemon=True)
    
    def RecvFunc(self):
        while self.recvEn:
            try:
                rs = self.mySerial.readline()
                self.sbuff.put(rs.decode())
                # print(rs.decode())
            except:
                pass
            
    def RecvPars(self, cmd):

        while not self.sbuff.empty():
            tstr = str(self.sbuff.get()).replace(',', ' ').split()
            
            if tstr:
                if cmd == 'QSPN' and tstr[0] == '+QSPN:':
                    self.Data['Network'] = tstr[1][1:-1]
                elif cmd == 'CGDCONT' and len(tstr) > 3:
                    if tstr[1] == '1':
                        self.Data['APN'] = tstr[3][1:-1]
                elif cmd == 'GSN' and len(tstr[0]) > 10:
                    self.Data['IMEI'] = tstr[0]
                elif cmd == 'CIMI' and len(tstr[0]) > 10:
                    self.Data['IMSI'] = tstr[0]
            
    def UpdateInfo(self):
        if not self.mySerial.is_open:
            self.mySerial.open()

        self.recvEn = True
        self.recvTh.start()
        
        self.mySerial.write('AT+QSPN\r'.encode())
        time.sleep(0.5)
        self.RecvPars('QSPN')
        
        self.mySerial.write('AT+CGDCONT?\r'.encode())
        time.sleep(0.5)
        self.RecvPars('CGDCONT')
        
        self.mySerial.write('AT+GSN\r'.encode())
        time.sleep(0.5)
        self.RecvPars('GSN')
        
        self.mySerial.write('AT+CIMI\r'.encode())
        time.sleep(0.5)
        self.RecvPars('CIMI')
        
        self.recvEn = False
        self.mySerial.cancel_read()
        self.recvTh.join()
        self.mySerial.close()
        
        korea = pytz.timezone('Asia/Seoul')
        utc_dt = datetime.datetime.utcnow()
        utc_dt = pytz.utc.localize(utc_dt)
        korea_dt = korea.normalize(utc_dt.astimezone(korea))
        self.Data['DateTime'] = korea_dt.strftime('%Y-%m-%d %H:%M:%S')

    # # APN 수동 업데이트 # 안써도 되는 함수
    # def ApnUpdateInfo(self, apn):
    #     self.mySerial.write(('AT+CGDCONT= 1,"IPV4V6","%s","0.0.0.0.0.0.0.0.0.0.0.0.0.0.0.0",0,0,0,0\r'%apn).encode()) # connect.cxn
    #     time.sleep(0.5)
    #     self.RecvPars('CGDCONT')