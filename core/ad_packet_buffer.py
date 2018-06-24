#!/usr/bin/python3


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


class ADObserver:

    def update(self, packet):
        assert isinstance(packet, ADPacket)


class ADPacketBuffer:

    def __init__(self, max_size=100):
        self.buffer = []
        self.observers = []

    def add_packet(self, packet):
        assert isinstance(packet, ADPacket)

        if len(self.buffer) >= 100:
            self.buffer = []

        if packet not in self.buffer:
            self.buffer.append(packet)
            for o in self.observers:
                o.update(packet)

    def add_observer(self, observer):
        assert isinstance(observer, ADObserver)

        if not (observer in self.observers):
            self.observers.append(observer)

    def del_observer(self, observer):
        assert isinstance(observer, ADObserver)

        if observer in self.observers:
            self.observers.remove(observer)
