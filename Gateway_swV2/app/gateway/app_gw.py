#!/usr/bin/env python3
"""
Empty NCP-host Example Application.
"""

# Copyright 2021 Silicon Laboratories Inc. www.silabs.com
#
# SPDX-License-Identifier: Zlib
#
# The licensor of this software is Silicon Laboratories Inc.
#
# This software is provided 'as-is', without any express or implied
# warranty. In no event will the authors be held liable for any damages
# arising from the use of this software.
#
# Permission is granted to anyone to use this software for any purpose,
# including commercial applications, and to alter it and redistribute it
# freely, subject to the following restrictions:
#
# 1. The origin of this software must not be misrepresented; you must not
#    claim that you wrote the original software. If you use this software
#    in a product, an acknowledgment in the product documentation would be
#    appreciated but is not required.
# 2. Altered source versions must be plainly marked as such, and must not be
#    misrepresented as being the original software.
# 3. This notice may not be removed or altered from any source distribution.

import argparse
import os.path
import sys
import queue
import threading
import time
import copy
import pytz
import datetime
import socket
import json
import requests

sys.path.append(os.path.join(os.path.dirname(__file__), "../.."))
from common.util import BT_XAPI, BluetoothApp, PeriodicTimer

# Characteristic values
CONN_INTERVAL_MIN = 80   # 100 ms
CONN_INTERVAL_MAX = 80   # 100 ms
CONN_SLAVE_LATENCY = 0   # no latency
CONN_TIMEOUT = 100       # 1000 ms
CONN_MIN_CE_LENGTH = 0
CONN_MAX_CE_LENGTH = 65535

SCAN_INTERVAL = 16       # 10 ms
SCAN_WINDOW = 16         # 10 ms
SCAN_PASSIVE = 1

# global EvtBuff
# EvtBuff = queue.Queue()

# global RecvBuff
# RecvBuff = queue.Queue()

class App(BluetoothApp):
    """ Application derived from generic BluetoothApp. """
    def __init__(self, apis=..., parser=None):
        super().__init__(parser=parser)
        
        self.EvtBuff = queue.Queue(1000) # queue 사이즈를 200 -> 1000 으로 임시 변경 20240215
        # self.RecvBuff = queue.Queue()
        
        self._parsThreadEn = True
        self.blelist = {}
        
        # self.sendThEn = True
        # self.sendTh = threading.Thread(target=self.SendProcess, daemon=True)
        # self.sendTh.start()
        
        self.myTh = threading.Thread(target=self.CheckDevice, daemon=True)
        self.myTh.start()
        
        # self._mywatchdogTimer = PeriodicTimer(period=1.0, target=self.myWatchdog)
        # self._mywatchdogTimer.start()
        # self._mywatchdog = 120
        
    def event_handler(self, evt):
        """ Override default event handler of the parent class. """
        # This event indicates the device has started and the radio is ready.
        # Do not call any stack command before receiving this boot event!
        if evt == "bt_evt_system_boot":
            # Set passive scanning on 1Mb PHY
            # self.lib.bt.scanner.set_mode(self.lib.bt.gap.PHY_PHY_1M, SCAN_PASSIVE)
            self.lib.bt.scanner.set_mode(self.lib.bt.gap.PHY_PHY_CODED, SCAN_PASSIVE)
            # Set scan interval and scan window
            # self.lib.bt.scanner.set_timing(self.lib.bt.gap.PHY_PHY_1M, SCAN_INTERVAL, SCAN_WINDOW)
            self.lib.bt.scanner.set_timing(self.lib.bt.gap.PHY_PHY_CODED, SCAN_INTERVAL, SCAN_WINDOW)
            # Set the default connection parameters for subsequent connections
            self.lib.bt.connection.set_default_parameters(
                CONN_INTERVAL_MIN,
                CONN_INTERVAL_MAX,
                CONN_SLAVE_LATENCY,
                CONN_TIMEOUT,
                CONN_MIN_CE_LENGTH,
                CONN_MAX_CE_LENGTH)

            # Start scanning - looking for thermometer devices
            self.lib.bt.scanner.start(
                # self.lib.bt.gap.PHY_PHY_1M,
                self.lib.bt.gap.PHY_PHY_CODED,
                self.lib.bt.scanner.DISCOVER_MODE_DISCOVER_GENERIC)
            self.conn_state = "scanning"
            self.conn_properties = {}

        # This event indicates that a new connection was opened.
        elif evt == "bt_evt_connection_opened":
            print("Connection opened")

        # This event indicates that a connection was closed.
        elif evt == "bt_evt_connection_closed":
            print("Connection closed")

        ####################################
        # Add further event handlers here. #
        ####################################

        # This event is generated when an advertisement packet or a scan response
        # is received from a responder
        elif evt == "bt_evt_scanner_scan_report":
            # global EvtBuff
            # self.EvtBuff.put(evt)
            # self.EvtBuff.put(copy.deepcopy(evt))
            
            try:
                self.EvtBuff.put_nowait(evt)
            except:
                self.log.exception('EvtBuff.put_nowait(evt) Error!!')
            
    def myWatchdog(self):
        # self.log.info('WatchDog - ' + str(self._mywatchdog))
        if self._mywatchdog > 0:
            self._mywatchdog = self._mywatchdog - 1
        else:
            EarTagempty = {
                "FrameType": "10",
                "SequenceNumber": 1,
                "Rssi": -50,
                "Time": "0000-00-00 00:00:00",
                "ScannerID": "70B3D517CF000019",
                "devEUI": "70B3D517C0000000",
                "battery": 0,
                "Temperature": {
                    "arr0": 0,
                    "arr1": 0,
                    "arr2": 0,
                    "arr3": 0,
                    "arr4": 0,
                    "arr5": 0
                },
                "AvrAcc": {
                    "arr0": 0,
                    "arr1": 0,
                    "arr2": 0,
                    "arr3": 0,
                    "arr4": 0,
                    "arr5": 0
                }
            }
            
            EarTagempty["ScannerID"] = self.ReadScannerID()
            
            korea = pytz.timezone('Asia/Seoul')
            utc_dt = datetime.datetime.utcnow()
            utc_dt = pytz.utc.localize(utc_dt)
            korea_dt = korea.normalize(utc_dt.astimezone(korea))
            EarTagempty["Time"] = korea_dt.strftime('%Y-%m-%d %H:%M:%S.%f')

            self._mywatchdog = 120
            
            if self._DataCallback:
                self._DataCallback(EarTagempty)
                
            
    
    def Stop(self):
        self.log.info('Stop - BLE')
        self.stop()
        # self._mywatchdogTimer.stop()
        
        self._parsThreadEn = False
        # self.sendThEn = False
        
        self.log.info('Join - myTh, sendTh')
        # self.sendTh.join()
        self.myTh.join()
                
    def ReadScannerID(self):
        # file = "/home/pi/Work/Farmpro_BLE_Gateway/GatewayConfig.json"
        # file = "/root/Python/GatewayConfig.json"
        file = os.path.join(os.path.dirname(__file__), "../../GatewayConfig.json")
        with open(file) as f:
            json_data = json.load(f)
            return json_data["GatewayID"]
        
        return "70B3D517CF000000"
            
    def CheckDevice(self):
        # global EvtBuff
        # global RecvBuff
        
        while self._parsThreadEn :
            # if self.EvtBuff.qsize() <= 0 :
            #     time.sleep(0.1)
            #     continue
            try:
                # evtt = self.EvtBuff.get(block=False, timeout=1.0)
                evtt = self.EvtBuff.get_nowait()
                
            except:
                # self.log.info('EvtBuff Error!!!')
                time.sleep(0.1)
                continue

            isNew = True
            
            try:
                if str(evtt.address).upper() in self.blelist:
                    if self.blelist[str(evtt.address).upper()] != evtt.data[42]:
                        self.blelist[str(evtt.address).upper()] = evtt.data[42]
                    else:
                        isNew = False
                else:
                    self.blelist[str(evtt.address).upper()] = evtt.data[42]
            except:
                isNew = False

            if isNew:
                val = {
                        "address": "",
                        "time": "",
                        "rssi": 0,
                        "data": ""
                    }
                val["address"] = copy.deepcopy(str(evtt.address).upper())
                val["rssi"] = copy.deepcopy(evtt.rssi)
                val["data"] = copy.deepcopy(evtt.data)
                
                korea = pytz.timezone('Asia/Seoul')
                utc_dt = datetime.datetime.utcnow()
                utc_dt = pytz.utc.localize(utc_dt)
                korea_dt = korea.normalize(utc_dt.astimezone(korea))
                val["time"] = korea_dt.strftime('%Y-%m-%d %H:%M:%S.%f')

                self._mywatchdog = 120

                # try:
                #     self.RecvBuff.put_nowait(val)
                # except:
                #     self.log.info('RecvBuff.put_nowait(val) Error')

                # print("Packet : " + str(evtt))
                
                if self._DataCallback:
                    self._DataCallback(self.MakeSendData(val))

                
                        
    # def SendProcess(self):
    #     # global RecvBuff
        
    #     while self.sendThEn:
    #         if self.RecvBuff.empty():
    #             time.sleep(0.1)
    #             continue
            
    #         try:
    #             # tdata = RecvBuff.get()
    #             tdata = self.RecvBuff.get_nowait()
    #         except:
    #             self.log.info('RecvBuff Error!!!')
    #             continue
            
    #         txdata = self.MakeSendData(tdata)
                    
    #         if self._DataCallback:
    #             self._DataCallback(txdata)
                
    #         self._mywatchdog = 120
                    
    def SetDataCallback(self, fucn):
        self._DataCallback = fucn
            
    def MakeSendData(self, element):
        EarTag = {
            "FrameType": "0",
            "SequenceNumber": 1,
            "Rssi": -50,
            "Time": "0000-00-00 00:00:00",
            "ScannerID": "70B3D517CF000019",
            "devEUI": "70B3D517C0000001",
            "battery": 0,
            "Temperature": {
                "arr0": 0,
                "arr1": 0,
                "arr2": 0,
                "arr3": 0,
                "arr4": 0,
                "arr5": 0
            },
            "AvrAcc": {
                "arr0": 0,
                "arr1": 0,
                "arr2": 0,
                "arr3": 0,
                "arr4": 0,
                "arr5": 0
            }
        }

        try:
            if len(element["data"]) == 45:
                EarTag["Rssi"] = element["rssi"]
                EarTag["Time"] = element["time"]
                EarTag["ScannerID"] = self.ReadScannerID()
                EarTag["devEUI"] = element["data"][9:17].hex()
                # EarTag["SequenceNumber"] = element["data"][42]
                EarTag["SequenceNumber"] = element["data"][43]
                EarTag["FrameType"] = str(element["data"][44])
                arrT = int.from_bytes(element["data"][17:19], byteorder='little', signed=True)/100
                EarTag["Temperature"]["arr0"] = round(arrT, 2)
                
                arrT = int.from_bytes(element["data"][19:21], byteorder='little', signed=True)/100
                EarTag["Temperature"]["arr1"] = round(arrT, 2)
                
                arrT = int.from_bytes(element["data"][21:23], byteorder='little', signed=True)/100
                EarTag["Temperature"]["arr2"] = round(arrT, 2)
                
                arrT = int.from_bytes(element["data"][23:25], byteorder='little', signed=True)/100
                EarTag["Temperature"]["arr3"] = round(arrT, 2)
                
                arrT = int.from_bytes(element["data"][25:27], byteorder='little', signed=True)/100
                EarTag["Temperature"]["arr4"] = round(arrT, 2)
                
                arrT = int.from_bytes(element["data"][27:29], byteorder='little', signed=True)/100
                EarTag["Temperature"]["arr5"] = round(arrT, 2)
                
                EarTag["AvrAcc"]["arr0"] = int.from_bytes(
                    element["data"][29:31], byteorder='little', signed=False)
                EarTag["AvrAcc"]["arr1"] = int.from_bytes(
                    element["data"][31:33], byteorder='little', signed=False)
                EarTag["AvrAcc"]["arr2"] = int.from_bytes(
                    element["data"][33:35], byteorder='little', signed=False)
                EarTag["AvrAcc"]["arr3"] = int.from_bytes(
                    element["data"][35:37], byteorder='little', signed=False)
                EarTag["AvrAcc"]["arr4"] = int.from_bytes(
                    element["data"][37:39], byteorder='little', signed=False)
                EarTag["AvrAcc"]["arr5"] = int.from_bytes(
                    element["data"][39:41], byteorder='little', signed=False)
                EarTag["battery"] = round(element["data"][41] / 10, 1)
                
                return EarTag
        except:
            pass
        
        return None
    
    
def CallbackParsingData(data):
    print("SEND : " + str(data))
    
# Script entry point.
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    # Instantiate the application.
    app = App(parser=parser)
    
    app.SetDataCallback(CallbackParsingData)
    
    # Running the application blocks execution until it terminates.
    app.run()
    
    app.Stop()
