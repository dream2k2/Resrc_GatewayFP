import os
import asyncio
import random
import json

from azure.iot.device.aio import IoTHubDeviceClient
from azure.iot.device.aio import ProvisioningDeviceClient
from azure.iot.device import constant, Message, MethodResponse
from datetime import date, timedelta, datetime

CONNECTION_STRING = "{HostName=CowManagementIotHub.azure-devices.net;DeviceId=sensor-a-001;SharedAccessKey=d1N3mEWWvpapjbjXuBGseAPiYyo/ST6i96ukg+E2Hs0=}"
DEVICE_ID = "{sensor-a-001}"

#####################################################
# Send STARTS
async def AzureSend(Data):
    print("[Azure] Connecting using Connection String ")
    device_client = IoTHubDeviceClient.create_from_connection_string(
        CONNECTION_STRING, product_info=DEVICE_ID
    )

    # Connect the client.
    await device_client.connect()

    ################################################
    # Send 
    msg = Message(json.dumps(Data))
    msg.content_encoding = "utf-8"
    msg.content_type = "application/json"
    print("[Azure] Sent message")
    await device_client.send_message(msg)

    # Finally, shut down the client
    await device_client.shutdown()

