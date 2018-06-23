#!/usr/bin/python
from time import gmtime, strftime
from bluepy.btle import Scanner, DefaultDelegate

INFINITY = 'infinity'


class ADData:

    def __init__(self, type_, info, data):
        self.type = type_
        self.info = info
        self.data = data

    def __str__(self):
        return 'DATA--------------------\ntype: ' + str(self.type) + '\ninfo: ' + self.info + '\ndata: ' + self.data + \
               '\n'

    def __repr__(self):
        return 'ADData(%s,%s,%s)' % (self.type, self.info, self.data)

    def __eq__(self, other):
        if isinstance(other, ADData):
            return (self.type == other.type) and (self.info == other.info) and (self.data == other.data)
        else:
            return False

    def __ne__(self, other):
        return not self.__eq__(other)

    def __hash__(self):
        return hash(self.__repr__())


class ADPacket:

    def __init__(self, date, time, sender_addr, ad_datas):
        self.date = date
        self.time = time
        self.sender_addr = sender_addr
        self.packet = set()

        assert isinstance(ad_datas, list)
        for d in ad_datas:
            assert isinstance(d, ADData)
            self.packet.add(d)

    def __str__(self):
        output = 'PACKET------------------\ndate: ' + self.date + '\ntime: ' + self.time + '\nsender addr: ' + \
                 self.sender_addr + '\n'
        for d in self.packet:
            output += d.__str__()
        output += '------------------------\n'
        return output

    def __repr__(self):
        return 'ADPacket(%s,%s)' % (self.sender_addr, self.packet)

    def __eq__(self, other):
        if isinstance(other, ADPacket):
            return (self.sender_addr == other.sender_addr) and (self.packet == other.packet)
        else:
            return False

    def __ne__(self, other):
        return not self.__eq__(other)

    def __hash__(self):
        return hash(self.__repr__())


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
        self.incoming_packets.add(packet)
        if self.debug:
            print(packet)

    def __init__(self, debug=False):
        self.allowed_addrs = set()
        self.incoming_packets = set()
        self.stop = False
        self.scanner = Scanner().withDelegate(self)
        self.debug = debug

    def enable_debug(self):
        self.debug = True

    def disable_debug(self):
        self.debug = False

    def set_filter(self, allowed_addrs):
        assert isinstance(allowed_addrs, list)
        self.allowed_addrs = allowed_addrs

    def write(self, data):
        print('Writing this data: ' + data)

    def listen(self, time):
        if time == INFINITY:
            while not self.stop:
                self.scanner.scan(10.0, passive=True)
        else:
            self.scanner.scan(time, passive=True)

    def stop_infinity_listen(self):
        self.stop = True
