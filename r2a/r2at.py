from r2a.ir2a import IR2A
from abc import ABCMeta, abstractmethod
from base.message import Message, MessageKind
from base.whiteboard import Whiteboard
from player.parser import *
import numpy
import time


class R2AT(IR2A):

    def __init__(self, id):
        IR2A.__init__(self, id)
        self.throughputs = []
        self.throughputs_peso = []
        self.request_time = 0
        self.qi = [] 
        self.contador = 0
        self.index = 15
        self.buffer_size = 0
        self.whiteboard = Whiteboard.get_instance()
 


    def handle_xml_request(self, msg):
        self.request_time = time.perf_counter()
        self.send_down(msg)


    def handle_xml_response(self, msg):
        parsed_mpd = parse_mpd(msg.get_payload())
        self.qi = parsed_mpd.get_qi()
        self.send_up(msg)
        


    def handle_segment_size_request(self, msg):

        tempo = (time.perf_counter() - self.request_time)
        vazao = (msg.get_bit_length()/tempo)
        self.contador += 1
        

        #buffer
        if len(self.whiteboard.get_playback_buffer_size()) > 0:
            self.buffer_size = self.whiteboard.get_playback_buffer_size()[-1][1]
        else:
            self.buffer_size = 0
        print(f" -----------------------> select = {self.index} ---- Size_request")
        if self.buffer_size >= 40 and self.index < 19:
            self.index += 1
        elif self.buffer_size <= 10 and self.index > 0:
            self.index -= 1
        print(f" -----------------------> select = {self.index} buffer = {self.buffer_size}---- Size_request")
        selected_qi = self.qi[self.index]

        msg.add_quality_id(self.qi[self.index])
        self.send_down(msg)


    def handle_segment_size_response(self, msg):
        print(msg.get_url())

        tempo = time.perf_counter() - self.request_time
        tamanho_bits = msg.get_bit_length()
        vazao = tamanho_bits/tempo

        self.throughputs.append(vazao)
        mi = sum(self.throughputs)/self.contador

        # para priorizar throughtputs recentes em comparação com os mais velhos, definimos 
        self.throughputs_peso.append(1/self.contador * (vazao - mi))
        sigma = sum(self.throughputs_peso)

        p = mi/(mi+sigma)
        desc = (1 - p) * self.qi[max(0, self.index-1)]
        cres = p * self.qi[min(19, self.index+1)]



        lst = numpy.asarray(self.qi)
        index = (numpy.abs(lst - desc + cres)).argmin()

        print(f" -----------------------> select = {self.index} ---- Size_Response")

        if self.buffer_size >= 50 and self.index < 19:
            self.index += 1
        elif self.buffer_size <= 10 and self.index > 0:
            self.index -= 1
        else:
            self.index = index

        print(f" -----------------------> select = {self.index} index = {index} buffer = {self.buffer_size} ---- Size_Response")



        print("")
        print(f">>>>>>>>>>>>>>>>>> Tempo = {tempo}")
        print(f">>>>>>>>>>>>>>>>>> Tamanho em bits = {tamanho_bits}")
        print(f">>>>>>>>>>>>>>>>>> Vazao = {vazao}")
        print(f">>>>>>>>>>>>>>>>>> Contador = {self.contador}")

        print(f"select = {self.index} ---- {self.qi[self.index]}")

        print("")

        self.send_up(msg)
        # pass


    def initialize(self):
        #SimpleModule.initialize(self)
        pass

    def finalization(self):
        #SimpleModule.finalization(self)
        pass
