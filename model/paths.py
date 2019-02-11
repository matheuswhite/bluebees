import os
import json


# file types
NETWORK_FILE_TYPE = '.network'
DEVICE_FILE_TYPE = '.device'

# create bluebees folder, if not exist
BLUEBEES_DIR_PATH = os.path.expanduser("~") + '/.bluebees/'
if not os.path.exists(BLUEBEES_DIR_PATH):
    os.mkdir(BLUEBEES_DIR_PATH)

# create net list, if not exist
NET_LIST_FILE_NAME = 'net_list'
if not os.path.exists(BLUEBEES_DIR_PATH + NET_LIST_FILE_NAME + NETWORK_FILE_TYPE):
    with open(BLUEBEES_DIR_PATH + NET_LIST_FILE_NAME + NETWORK_FILE_TYPE, 'w') as net_list_file:
        net_list = {
            'net_list': []
        }
        json.dump(net_list, net_list_file)

# create device list, if not exist
DEVICE_LIST_FILE_NAME = 'device_list'
if not os.path.exists(BLUEBEES_DIR_PATH + DEVICE_LIST_FILE_NAME + DEVICE_FILE_TYPE):
    with open(BLUEBEES_DIR_PATH + DEVICE_LIST_FILE_NAME + DEVICE_FILE_TYPE, 'w') as device_list_file:
        device_list = {
            'device_list': []
        }
        json.dump(device_list, device_list_file)
