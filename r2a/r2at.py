

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
        self.qi = [] #Vetor que armazena qualidade dos video 
        self.contador = 0 #Descreve quantas requisições já foram, totalizando 597 
        self.index = 15 #Usuários consideram menos prejudicial esperar no começo, sendo assim foi considerado uma qualidade boa, mas não o máximo para que essa espera não seja grande
        self.buffer_size = 0
        self.whiteboard = Whiteboard.get_instance()
        self.listMI = []
 


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

        if self.buffer_size >= 40 and self.index < 19:
            self.index += 1
        if self.buffer_size <= 10 and self.index > 0:
            self.index -= 1

        selected_qi = self.qi[self.index]

        msg.add_quality_id(self.qi[self.index])
        self.send_down(msg)


    def handle_segment_size_response(self, msg):
        print(msg.get_url())

        tempo = time.perf_counter() - self.request_time
        tamanho_bits = msg.get_bit_length()
        vazao = tamanho_bits/tempo

        #Média da taxa de transferência
        self.throughputs.append(vazao)
        mi = sum(self.throughputs)/self.contador
        self.listMI.append(mi)

        #Média com peso, usada para priozar throughout mais recentes. 
        #self.throughputs_peso.append((1/self.contador) * abs(vazao - mi))
        print(self.contador)
        # if vazao != mi: 
        #     self.throughputs_peso.append(1/(self.contador * abs(vazao - mi)))
        #self.throughputs_peso.append(self.contador/596 * abs(vazao - mi))
        i = 0
        sigmaList = []
        for item in self.throughputs:
            sigmaList.append((i/self.contador) * abs(item - mi))
            i += 1
        #self.throughputs_peso.append(self.contador * abs(vazao - mi))
        
        # sigma = sum(self.throughputs_peso)
        sigma = sum(sigmaList)


        # P é a probabilidade de que 
        p = mi/(mi+sigma)
        desc = (1 - p) * self.qi[max(0, self.index-1)]
        cres = p * self.qi[min(19, self.index+1)]
        
        array = numpy.array(self.qi)
        difference_array = []
        for i in range(len(self.qi)):
            if self.qi[i] < (desc + cres):
                pass
            else: 
                index = i
                break

        # difference_array2 = numpy.absolute(array - desc + cres)
        # index = difference_array2.argmin()

        # print(difference_array)
        # print(difference_array2)
        #index = numpy.argmin(lst - abs(desc + cres))


        if self.buffer_size >= 40 and self.index < 19:
            self.index = index + 1
        elif self.buffer_size <= 10 and self.index > 0:
            self.index = index - 1
        # else:
        #     self.index = index
        # else:
        #     if index < 19 and self.buffer_size >= 30:
        #         self.index = index + 1
        #     else:
        else:
            self.index = index

        print(f"INDEX SELECT = {index}")
        # print(lst - desc + cres)
        # print(lst)

        self.send_up(msg)



    def initialize(self):
        #SimpleModule.initialize(self)
        pass

    def finalization(self):
        #SimpleModule.finalization(self)
        pass
