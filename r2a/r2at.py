# Alunos:
    # Tais Alves Oliveira - 190117176
    # 

# Disciplina:
    # Dep. Ciência da Computação - Universidade de Brasília (UnB),
    # Redes de Computadores - 2022.2

# Implementação:
    # > Finalization module Player

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
        self.throughput = 0
        self.request_time = 0
        self.qi = []
  
        self.index = 4 

        self.whiteboard = Whiteboard.get_instance()

        self.uso_buffer = 0


    def handle_xml_request(self, msg):

        self.send_down(msg)

    def handle_xml_response(self, msg):
        parsed_mpd = parse_mpd(msg.get_payload())
        self.qi = parsed_mpd.get_qi()

        self.send_up(msg)
        
    def handle_segment_size_request(self, msg):
        self.request_time = time.perf_counter()

        #atribui tamanho do buffer:
        if len(self.whiteboard.get_playback_buffer_size()) > 0:
            buffer_size = self.whiteboard.get_playback_buffer_size()[-1][1]
        else:
            buffer_size = 0
        
        #Verifica se o buffer foi usado e quanto tempo levou para isso:
        buffer = False
        tamanho = len(self.whiteboard.get_playback_segment_size_time_at_buffer())
        if tamanho > 0 :
            tempo_espera = self.whiteboard.get_playback_segment_size_time_at_buffer()[-1]
            if self.uso_buffer < tamanho:
                self.uso_buffer = tamanho
                buffer = True
            else:
                buffer = False
        else:
            tempo_espera = 1
            

        #Ajusta o index e retorna um numero valido
        self.index = retorna_index_valido(self.index + ajuste_buffer(buffer_size, tempo_espera, buffer))

        msg.add_quality_id(self.qi[self.index])

        self.send_down(msg)


    def handle_segment_size_response(self, msg):

        # Adiciona a vazão atual na lista
        self.throughput = msg.get_bit_length()/(time.perf_counter() - self.request_time) 
        self.throughputs.append(self.throughput)

        momento = msg.get_segment_id()
        media = mi(self.throughputs, momento)
        peso = sigma(self.throughputs, momento, media)
        probabilidade = p(media, peso)

        k = tau(probabilidade, self.qi, self.index) + teta(probabilidade, self.qi, self.index) # k é a constante dada somando a probabilidade da qualidade aumentar ou diminuir

        self.index = index_da_menor_diferenca(self.qi, k)

        self.send_up(msg)

    def initialize(self):
        #SimpleModule.initialize(self)
        pass

    def finalization(self):
        #SimpleModule.finalization(self)
        pass


def mi(lista, momento):
    # Média da taxa de transferencia
    return sum(lista)/momento


def sigma(lista, momento, media):
    # Peso usado para priozar vazões mais recentes. 
    i = 1
    sigmaList = []
    for item in lista:
        sigmaList.append((i/momento) * abs(item - media))
        i += 1
       
    return sum(sigmaList)


def p(sigma, mi):
    # Probalidade entre 0 e 1 que estima a disposição de mudar de qualidade:
    # Um p proximo de 1, mostra uma rede estável 
    # um p proximo de 0, mostra uma rede instável
    return mi/(mi+sigma)


def tau(p, qualidades, index):
    #se o index não for 0, analisa a possibilidade da qualidade de descrescer
    if index != 0:
        index -= 1
    return (1-p) * qualidades[index]


def teta(p, qualidades, index):
    #se o index não for 19, analisa a possibilidade da qualidade de crescer
    if index != 19:
        index += 1
    return p * qualidades[index]


def index_da_menor_diferenca(lista, k):
    #compara todos os elementos da lista de qualidades com a constante estabelecida e devolve a menor diferença
    lista_comparativa = []
    for item in lista:
        lista_comparativa.append(abs(item - k))
    return lista_comparativa.index(min(lista_comparativa))


def ajuste_buffer(buffer_size, tempo_espera,buffer):
    #Comparando o buffer e a ultima mudança que teve na lista de buffer, cria um numero para ajustar o index para mais ou para menos
    ajuste_buffer = -1
    if buffer_size < 10:
        ajuste_buffer -= 1
        if buffer_size < 5:
            ajuste_buffer -= 1
    elif buffer_size > 30:
        ajuste_buffer += 1
        if buffer_size > 45:
            ajuste_buffer += 1
            if buffer_size > 55:
                ajuste_buffer += 2
    if buffer:
        ajuste_buffer -= 1
        if tempo_espera < 1:
            ajuste_buffer -= 1
        
    return ajuste_buffer

def retorna_index_valido(index):
    #Avalia se o Index está dentro da lista, se não retorna indice da extremidade
    if index < 0:
        index = 0
    elif index > 19:
        index = 19
    return index
