import RPi.GPIO as GPIO

class Motor():
    def __init__(self) -> None:
        self.DIR1_PIN = 20
        self.DIR2_PIN = 21
        self.PWM_PIN = 12
        self.duty_cycle = 0
        self.__status = 'Livre'
        
        GPIO.setmode(GPIO.BCM)
        GPIO.setwarnings(False)
        
        GPIO.setup(self.DIR1_PIN, GPIO.OUT)
        GPIO.setup(self.DIR2_PIN, GPIO.OUT)
        GPIO.setup(self.PWM_PIN, GPIO.OUT)
        
        self.pwm = GPIO.PWM(self.PWM_PIN, 1000)  # 1000 Hz de frequência inicial
        self.pwm.start(0)  # duty cycle inicial de 0%
        self.status = 'Livre'
      
    def upElevador(self):
        GPIO.output(self.DIR1_PIN, GPIO.HIGH)
        GPIO.output(self.DIR2_PIN, GPIO.LOW)
        #self.status = 'Subindo'
    
    def downElevador(self):
        GPIO.output(self.DIR1_PIN, GPIO.LOW)
        GPIO.output(self.DIR2_PIN, GPIO.HIGH)
        #self.status = 'Descendo'
    
    def breakElevador(self):
        GPIO.output(self.DIR1_PIN, GPIO.HIGH)
        GPIO.output(self.DIR2_PIN, GPIO.HIGH)
        #self.status = 'Parado'
    
    def setStatus(self, estado):
        self.status = estado
    
    def getStatus(self):
        return self.status
    
    def setDutyCycle(self, valor):
        self.pwm.ChangeDutyCycle(valor)
        
    def moveMotor(self, valor):
        self.setDutyCycle(abs(valor))
        if valor < 0:
            self.downElevador()
        elif valor > 0:
            self.upElevador()
        else:
            self.breakElevador()
            self.setStatus('Parado')

