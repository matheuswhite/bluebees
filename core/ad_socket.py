#!/usr/bin/python3
from time import gmtime, strftime
from bluepy.btle import Scanner, DefaultDelegate
from threading import Lock
from core.ad_packet_buffer import ADPacket, ADData, ADPacketBuffer


class ADSocket(DefaultDelegate):

    def handleDiscovery(self, dev, isNewDev, isNewData):
        date = strftime('%d-%m-%Y', gmtime())
        time = strftime('%H:%M:%S', gmtime())
        sender_addr = dev.addr
        scan_data = dev.getScanData()
        ad_datas = list()

        for sd in scan_data:
            type_ = sd[0]
            info = sd[1]
            data = sd[2]
            ad_data = ADData(type_, info, data)
            ad_datas.append(ad_data)

        packet = ADPacket(date, time, sender_addr, ad_datas)

        self.incoming_packets_lock.acquire()
        self.incoming_packets.add_packet(packet)
        self.incoming_packets_lock.release()

        if self.debug:
            print(self.name + '\n' + str(packet))

    def __init__(self, debug=False, name='Default'):
        self.incoming_packets = ADPacketBuffer()
        self.incoming_packets_lock = Lock()
        self.scanner = Scanner().withDelegate(self)
        self.debug = debug
        self.name = name

    def enable_debug(self):
        self.debug = True

    def disable_debug(self):
        self.debug = False

    def write(self, data):
        print('Writing this data: ' + data)

    def listen(self, time):
        self.scanner.scan(time, passive=True)

    def add_oberserver(self, observer):
        self.incoming_packets_lock.acquire()
        self.incoming_packets.add_observer(observer)
        self.incoming_packets_lock.release()

    def del_observer(self, observer):
        self.incoming_packets_lock.acquire()
        self.incoming_packets.del_observer(observer)
        self.incoming_packets_lock.release()
