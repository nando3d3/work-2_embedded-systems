from comunicacao.Uart import Uart
from comunicacao.CodigoModbus import getCodigo
from modelo.Motor import *
from modelo.Pid import PID
from modelo.Sensor import Sensor
from modelo.Elevador import Elevador
from i2c.Bmp280 import bmp280_device
from i2c.Lcd import lcd
import time
import struct
import threading

motor = Motor()
sensor = Sensor()
uart = Uart()
pid = PID()
bmp280= bmp280_device()
display_lcd = lcd()
elevador = Elevador()

uart_lock = threading.Lock()

running = True
elevador_movendo = False

andares = ['ST', 'S1', 'S2', 'S3']
def main():
      
    try:
        sensor.start()
        displayStatus_thread = threading.Thread(target=displayStatus)
        global elevador_pos
        elevador_pos = calibracao()
        displayStatus_thread.start()
        recebeRegistrador()
        
    except Exception as e:
        print('erro: ', e)
        encerra()
    except KeyboardInterrupt:
        encerra()

def recebeRegistrador():
    global running
    while running:
        elevador.setRegistrador(comando('le_registrador'))
        elevador.trataRegistrador()
            
        if 'emergency' in elevador.getFila():
                botaoEmergencia()
        elif len(elevador.getFila()) != 0 and not elevador_movendo:
            andar = elevador.getFila()[0]
            moveElevador_thread = threading.Thread(target=moveElevador, args=(andar,))
            moveElevador_thread.start()
        time.sleep(0.05)

 
def moveElevador(andar):
    global elevador_movendo
    elevador_movendo = True
    pos_atual = comando('solicita_encoder')
    if pos_atual - elevador_pos[andar] > 0:
        motor.setStatus('Descendo')
    elif pos_atual - elevador_pos[andar] < 0:
        motor.setStatus('Subindo')
    
    referencia = elevador_pos[andar]
    pid.atualiza_referencia(referencia)
    print('Indo para ', andar)
    potencia = pid.controle(comando('solicita_encoder'))
    diff_posicao = 500
    while diff_posicao > 3 and running:
        saida = comando('solicita_encoder')
        potencia = pid.controle(saida)
        motor.moveMotor(potencia)
        comando('sinal_PWM', int(abs(potencia)))
        diff_posicao = abs(saida - referencia)
        time.sleep(0.2)
    if running:
        motor.setStatus('Parado')
        motor.moveMotor(0)
        desligaBotao(andar)
        elevador.removeFila()
        print('Porta aberta')
        contagemPorta()   #aguarda 3 segundos para fechar a porta
        elevador_movendo = False

def desligaBotao(andar):
    botoes = elevador.getAndarBotao()[andar]
    for botao in botoes:
        comando('escreve_registrador', botao = botao)
    
def comando(mensagem, valor = 0, botao = None):
    if running:
        if mensagem == 'solicita_encoder':
            with uart_lock:
                cmd = getCodigo(mensagem)
                uart.escreverEncoder(cmd, len(cmd))

                response = uart.lerEncoder()
                response = struct.unpack('i', response)[0]
                return response  
        
        if mensagem == 'sinal_PWM':
            with uart_lock:
                cmd = getCodigo(mensagem, valor)
                uart.escreverEncoder(cmd, len(cmd))
                uart.lerEncoder(5)
        
        if mensagem == 'temperatura':
            with uart_lock:
                #print('solicitou temp')
                cmd = getCodigo(mensagem, valor)
                uart.escreverEncoder(cmd, len(cmd))
                uart.lerEncoder(5)
                
        if mensagem == 'le_registrador':
            with uart_lock:
                cmd = getCodigo(mensagem)
                uart.escreverEncoder(cmd, len(cmd))
                response = uart.lerEncoder(15, True)
                
                return response
        if mensagem == 'escreve_registrador':
            with uart_lock:
                cmd = getCodigo(mensagem, valor, botao)
                uart.escreverEncoder(cmd, len(cmd))
                uart.lerEncoder(5, True)
    
def displayStatus():
    global running
    print('display iniciado...')
    display_lcd.lcd_clear()
    andar = -1
    while running:
        display_lcd.lcd_display_string('', 2)
        try:
            temperatura = bmp280.get_temp()
        except:
            pass
        if len(elevador.getFila()) != 0:
            andar = elevador.getFila()[0] 
            andar = andar.replace('S', 'A')
            display_lcd.lcd_display_string(f'{motor.getStatus()}: ' + andar, 2)
        display_lcd.lcd_display_string('Temp: '+ str(temperatura) + ' C', 1)
        
        comando('temperatura', temperatura)
        time.sleep(1)
        
    display_lcd.lcd_clear()

def calibracao():
    
    andares = ['ST', 'S1', 'S2', 'S3']
    
    print('calibrando')
    motor.setStatus('Calibrando...')
    pos = {}
    resp = comando('solicita_encoder')
    pid.atualiza_referencia(25000)
    
    if 25000 - resp < resp:
        motor.moveMotor(100)
        while resp < 25000:
            resp = comando('solicita_encoder')
        motor.moveMotor(0)
        time.sleep(1)
        print('descendo...')
        motor.moveMotor(-5)
    else:
        motor.moveMotor(-100)
        while resp > 0:
            resp = comando('solicita_encoder')
        motor.moveMotor(0)
        time.sleep(1)
        print('subindo...')
        motor.moveMotor(5)
    
    print('procurando posicoes...')
    print('[')
    
    while not all(key in pos for key in andares):
        andar_detectado = sensor.active_sensor
        if andar_detectado in andares and andar_detectado not in pos:
            resp_list = []
            while sensor.active_sensor == andar_detectado:
                resp = comando('solicita_encoder')
                resp_list.append(resp)
                
            if len(resp_list) != 0:
                pos_media = int(sum(resp_list)/ len(resp_list))
                pos[andar_detectado] = pos_media
                print(f'Andar {andar_detectado}: {pos_media}')
    
    print(']\ncalibracao finalizada\n')
    motor.moveMotor(0)
    return pos

def botaoEmergencia():
    print('Botao de emergencia pressionado')
    for andar in andares:
        desligaBotao(andar)
    encerra()

def contagemPorta():
    # contagem regressiva de 3 segundos
    for i in range(3, 0, -1):
        print(i, end=' ', flush=True)
        time.sleep(1)
    print('Porta fechada')

def encerra():
    uart.desconectar()
    global running
    motor.moveMotor(0)
    running = False
    sensor.stop()
    sensor.join()
    #GPIO.cleanup()

if __name__ == "__main__":
    main()