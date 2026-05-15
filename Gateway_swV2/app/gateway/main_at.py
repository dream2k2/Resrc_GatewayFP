
# Quetel gateway command
# python3 /root/Gateway_swV2/app/gateway/main_basic.py /dev/ttyS1

import os
import os.path
import sys
import argparse
from app_gw import App
import json
import time
import threading
import heartbeat
import requests
import logging
import farmproAT

sys.path.append(os.path.join(os.path.dirname(__file__), "../.."))
sys.path.append(os.path.join(os.path.dirname(__file__), "../../common"))

import onionGpio
import util

global myApp
myApp = None

global atApp
atApp = None

ble_reset = onionGpio.OnionGpio(11)
ble_reset.setOutputDirection()

file = os.path.join(os.path.dirname(__file__), "../../GatewayConfig.json")
with open(file) as f:
    configjson = json.load(f)
    f.close()

def HWresetBLE():
    ble_reset.setValue(0)
    time.sleep(0.5)
    ble_reset.setValue(1)
    time.sleep(0.5)

def StartGPS():
    os.system('o2lte gnss enable')

def GetGPSdata():
    try:
        stream = os.popen('ubus call gps info')
        output = json.loads(stream.read())
        if not "latitude" in output:
            # output = {
            #     "age": 0,
            #     "latitude": 0,
            #     "longitude": 0,
            #     "elevation": "20.9",
            #     "course": "7.5",
            #     "speed": "0.0"
            # }
            # file = os.path.join(os.path.dirname(__file__), "../../GatewayConfig.json")
            # with open(file) as f:
            #     tj = json.load(f)
            #     output["latitude"] = tj["latitude"]
            #     output["longitude"] = tj["longitude"]
                
            # output = json.dumps(output)
            return json.dumps(configjson)
        else:
            configjson["latitude"] = output["latitude"]
            configjson["longitude"] = output["longitude"]
            
            return json.dumps(output)
    except:
        pass
        
    return json.dumps({
                "age": 0,
                "latitude": 0,
                "longitude": 0,
                "elevation": "20.9",
                "course": "7.5",
                "speed": "0.0"
            })

# def ReadServerInfo():
#     # file = "/home/pi/Work/Farmpro_BLE_Gateway/GatewayConfig.json"
#     # file = "/root/Python/GatewayConfig.json"
#     # file = os.path.join(os.path.dirname(__file__),
#     #                     "../../GatewayConfig.json")
#     # with open(file) as f:
#     #     json_data = json.load(f)
#     #     return json_data["Connect"]
    
#     return configjson["Connect"]
global SendCount
SendCount = 1
def SendHeartbeat():
    global SendCount
    global atApp
    
    # hb = heartbeat.HeartBeat()
    # hb.UpdateInfo()
    atApp.UpdateInfo()
    
    gps = GetGPSdata()
    gpsjson = json.loads(gps)
    
    try:
        if gpsjson["latitude"] and gpsjson["longitude"]:
            # hb.Data['latitude'] = gpsjson["latitude"]
            # hb.Data['longitude'] = gpsjson["longitude"]
            atApp.Data['latitude'] = gpsjson["latitude"]
            atApp.Data['longitude'] = gpsjson["longitude"]
    except:
        pass

    # hb.Close()
    
    # print(json.dumps(atApp.Data, indent=4))
    
    # try:
    #     headers = {'Content-Type': 'application/json; charset=utf-8'}
    #     # url = ReadServerInfo()
    #     url = configjson["Connect"]
    #     response = requests.put(url, headers=headers, data=json.dumps(hb.Data, indent=4, sort_keys=True), timeout=120)
    # finally:
    #     if response:
    #         print('response:', response.status_code)
    #     else:
    #         print('Response value Error!')

    main_send(atApp.Data)
    
    if SendCount <= 0:
        # sys.exit()
        # if myApp:
        #     myApp.Stop()
        # pid = os.getpid()
        # os.kill(pid, 2)
        
        os.system('reboot now')
            
        # restart_main()
    else:
        SendCount = 0

def CallbackParsingData(data):
    global SendCount
    
    if data == None:
        return
    
    gps = GetGPSdata()
    gpsjson = json.loads(gps)
    
    try:
        if gpsjson["latitude"] and gpsjson["longitude"]:
            if int(data['FrameType']) == 30:
                data['FrameType'] = '40'
                data['latitude'] = gpsjson["latitude"]
                data['longitude'] = gpsjson["longitude"]
    except:
        pass
    
    # print('GPS - ', gps)
    # print("SEND : " + json.dumps(data, indent=4))
    
    # try:
    #     headers = {'Content-Type': 'application/json; charset=utf-8'}
    #     # url = ReadServerInfo()
    #     url = configjson["Connect"]
    #     response = requests.put(url, headers=headers, data=json.dumps(data, indent=4, sort_keys=True), timeout=120)
    # finally:
    #     if response:
    #         print('response:', response.status_code)
    #     else:
    #         print('Response value Error!')

    main_send(data)
            
    SendCount = SendCount + 1

global sendlock
sendlock = False
def main_send(send_data):
    global atApp
    global sendlock
    while(sendlock):
        time.sleep(0.1)

    sendlock = True

    response = None

    mylog = logging.getLogger('Farmpro')
    
    mylog.info("SEND : " + json.dumps(send_data, indent=4))

    # try:
    #     headers = {'Content-Type': 'application/json; charset=utf-8'}
    #     # url = ReadServerInfo()
    #     url = configjson["Connect"]
    #     response = requests.put(url, headers=headers, data=json.dumps(send_data, indent=4, sort_keys=True), timeout=60)
    # except:
    #     pass

    # if response:
    #     mylog.info('response:' + str(response.status_code))
    # else:
    #     mylog.info('Response value Error!')
    
    atApp.OpenTCP()
    atApp.SendTCP(Data=send_data)
    atApp.CloseTCP()

    sendlock = False
            
def restart_main():  
    print("AutoRes is starting")
    executable = sys.executable
    args = sys.argv[:]
    args.insert(0, sys.executable)

    time.sleep(1)
    print("Respawning")
    os.execvp(executable, args)
    
# Script entry point.
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    
    atApp = farmproAT.FarmproAT()
    
    tip = str(configjson['Connect']).split("/")
    ttip = tip[2].split(":")
    print(ttip)
    
    atApp.tcp_ip = ttip[0]
    atApp.tcp_port = ttip[1]
    
    HWresetBLE()
    StartGPS()
    
    # wait ble booting time
    time.sleep(1)
    
    # SendHeartbeat()
    # hbtimer = util.PeriodicTimer(3600, SendHeartbeat) # heatbeat 임시 주석
    # hbtimer.start() # heatbeat 임시 주석
    SendHeartbeat()

    time.sleep(10)
    SendHeartbeat()
    
    # Instantiate the application.
    myApp = App(parser=parser)
    
    myApp.SetDataCallback(CallbackParsingData)
    
    try:
        # Running the application blocks execution until it terminates.
        myApp.run()

    finally:
        myApp.Stop()
        print("App Stoped!")
        
        
        
        # sys.exit()
        restart_main()
