import serial
import time
import sys

if __name__ == '__main__' :
    argv = sys.argv
    
    if argv[1]:
        print(argv[1])
        mySerial = serial.Serial('/dev/ttyS2', 115200, timeout=0.1)
        time.sleep(1)
        
        if not mySerial.is_open:
            mySerial.open()
        
        mySerial.write('\r'.encode())
        mySerial.write(argv[1].encode())
        mySerial.write('\r'.encode())
        
        isrun = True
        timecnt = 100
        
        while isrun and timecnt:
            try:
                rs = mySerial.readline(100)
                if rs:
                    print(rs.decode())
                    
                    if 'OK' in rs.decode() or 'ERROR' in rs.decode():
                        isrun = False
                        
            except KeyboardInterrupt:
                isrun = False
                break
            except TimeoutError:
                print('Time Out')
                isrun = False
                break
            
            timecnt = timecnt - 1
            
        mySerial.close()
        print('Serial Close!!')
    
    sys.exit()