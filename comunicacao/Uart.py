import serial
import time

from .Crc16 import *

class Uart:
    def __init__(self):
        self.serial = None
        self.connected = False
        
    def conectar(self):
        if self.serial is not None and self.serial.is_open:
            self.serial.close()
            
        try:
            self.serial = serial.Serial("/dev/serial0", 115200) # open serial port
            self.connected = True
            print('Conexao UART')
        except:
            print('Erro UART')
            
    def desconectar(self):
        if self.serial is not None and self.serial.is_open:
            self.serial.close()
            self.connected = False
            print('Desconexao UART')
    
    '''
    verifica se o valor do CRC no final do buffer corresponde ao CRC calculado dos bytes anteriores no buffer
    '''
    def validate_crc(self, buffer, buffer_size):
        crc_size = 2  # CRC tem 2 bytes
        
        if len(buffer) < crc_size:
            return False  # buffer muito pequeno para conter um CRC válido
        
        # bytes do buffer que contêm o CRC
        crc_buf = buffer[-crc_size:]
        # calcula o valor do CRC para os bytes no buffer, excluindo o CRC
        crc = calcula_crc(buffer[:-crc_size], buffer_size - crc_size).to_bytes(crc_size, 'little')
        
        return crc_buf == crc
    
    '''
    realiza a leitura de dados do encoder via conexao serial, 
    valida o CRC e retorna os dados ou mensagens de erro.
    '''      
    def lerEncoder(self, tam = 9, botao = False):
        try:
            if not self.connected:
                self.conectar()
            
            buffer = self.serial.read(tam)
            tamanho = len(buffer)
            dados = buffer[3:-2]
            
            if botao:
                dados = buffer[2:-2]
                #return dados
            #print(f"Retorno: {buffer} -> {dados} : {tamanho}")
            
            if self.validate_crc(buffer, tamanho):
                return dados
            else:
                print('Dados incorreta: ', buffer)
        except Exception as e:
            return f'Erro na leitura: {str(e)}'
    
    def escreverEncoder(self, msg, tam):
        if not self.connected:
            self.conectar()
        
        try:
            msg1 = msg
            msg2 = calcula_crc(msg1, tam).to_bytes(2, 'little')
            msg_final = msg1 + msg2
            self.serial.write(msg_final)
        except:
            print('erro ao escrever')