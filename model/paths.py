import os
import json


# file types
NETWORK_FILE_TYPE = '.network'

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
