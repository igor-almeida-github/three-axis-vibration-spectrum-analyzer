#define MPU_Addr 0x68

//*****************Protótipos_de_funções****************************************
void I2C_Start(void);                                                           // Essa função inicializa a start condition no barramento I2C
void I2C_Write(unsigned char i2c_byte);                                         // Transmite dados pela I2C
void I2C_Repeated_Start(void);                                                  // Sinal I2C repeated start
void I2C_Stop(void);                                                            // Essa função inicializa a stop condition no barramento I2C
unsigned char I2C_Read(unsigned char master_ack);                               // Função para a leitura da I2C e envio do bit ACK
void EUSART_init(void);                                                         // Essa função inicializa o módulo EUSART do pic16f883
void EUSART_write_char(unsigned char msg);                                      // Essa função envia um único byte pela serial EUSART
void EUSART_write_text(unsigned char*string);                                   // Essa função envia uma string de texto inteira pela eusart, até encontrar o caracter null

void main() {
    //*************Declaração_de_variáveis_de_escopo_local**********************
    int  ACCEL_XOUT=0, ACCEL_YOUT=0, ACCEL_ZOUT=0;
    unsigned int timer;
    ANSEL = 0x00;                                                               // Todas as portas são digitais AN0 até AN7
    ANSELH = 0x00;                                                              // Todas as portas são digitais AN8 até AN13
    TRISA = 0xFF;                                                               // Todas as IOs do PORTA são input
    TRISB = 0xFF;                                                               // Todas as IOs do PORTB são input
    TRISC = 0xFF;                                                               // Todas as IOs do PORTC são input
    TRISE = 0xFF;                                                               // Todas as IOs do PORTE são input

    //*************Configurações_EUSART*****************************************
    BAUDCTL.BRG16=1;
    SPBRGH=0x00;
    SPBRG=0x21;                                // Baud rate de 115200
    RCSTA=0x90;                                // Serial port habilitado, recepção de 8 bits, habilita recepção.
    TXSTA=0x24;                                // Modo de transmissão de 8 bits, eusart no modo assíncrono, high speed baud rate, habilita transmissão.

    //*************Configurações_I2C********************************************
    SSPSTAT=0x00;                                                               // Controle da taxa de varredura para modo de alta velocidade (400kz)
    SSPCON=0x28;                                                                // Habilita MSSP no modo master clock = Fosc/(4*(SSPADD+1))
    SSPCON2=0x00;                                                               // Não inicia nada ainda, permance em idle state
    SSPADD = 0x09;                                                              // I2C 400khz
    
    //*************Configurações_timer_1****************************************
    T1CON = 0x00;                                                               // Clock interno, prescale de 1, timer desligado.
    delay_ms(200);
    
    T1CON.TMR1ON = 1;                                                           // Inicia o timer 1
    
    for(;;){
    
        //**************************Le_dados_do_MPU*****************************
        I2C_Start();
        
        I2C_Write((MPU_Addr<<1)|0);                                             // Endereço do mpu + bit W
        while(SSPCON2.ACKSTAT){                                                 // Equanto slave não acknowledge
            if (PIR1.TMR1IF){                                                   // Se o timer 1 der overflow
                PIR1.TMR1IF = 0;                                                // Reseta a flag do timer 1
                I2C_Write((MPU_Addr<<1)|0);                                     // Endereço do mpu + bit W
            }
        }
        I2C_Write(0x3B);                                                        // ACCEL_XOUT_H: endereço do registro do MPU a ser lido primeiro
        I2C_Repeated_Start();                                                   // Sinal I2C repeated start
        I2C_Write((MPU_Addr<<1)|1);                                             // Envia o endereço do MPU +  R

        ACCEL_XOUT=I2C_Read(0)<<8;                                              // Lê ACCEL_XOUT_H e ACCEL_XOUT_L, envia acknowledge bit
        ACCEL_XOUT+=I2C_Read(0);
        EUSART_write_char(*((unsigned char*)&ACCEL_XOUT+1));                    // Envia ACCEL_XOUT_H e ACCEL_XOUT_L pela serial
        EUSART_write_char(*((unsigned char*)&ACCEL_XOUT));
        
        ACCEL_YOUT=I2C_Read(0)<<8;                                              // Lê ACCEL_YOUT_H e ACCEL_YOUT_L, envia acknowledge bit
        ACCEL_YOUT+=I2C_Read(0);
        EUSART_write_char(*((unsigned char*)&ACCEL_YOUT+1));                    // Envia ACCEL_YOUT_H e ACCEL_YOUT_L pela serial
        EUSART_write_char(*((unsigned char*)&ACCEL_YOUT));
        
        ACCEL_ZOUT=I2C_Read(0)<<8;                                              // Lê ACCEL_ZOUT_H e ACCEL_ZOUT_L, envia NOT acknowledge bit
        ACCEL_ZOUT+=I2C_Read(1);
        EUSART_write_char(*((unsigned char*)&ACCEL_ZOUT+1));                    // Envia ACCEL_ZOUT_H e ACCEL_ZOUT_L pela serial
        EUSART_write_char(*((unsigned char*)&ACCEL_ZOUT));
        
        I2C_Stop();

        EUSART_write_char(*((unsigned char*)&timer+1));                         // Envia tempo pela serial
        EUSART_write_char(*((unsigned char*)&timer));

        EUSART_write_char(0x0D);                                                // CR
        EUSART_write_char(0x0A);                                                // Nova linha LF(Line feed))
        
        T1CON.TMR1ON = 0;
        timer = TMR1L + (TMR1H<<8);
        TMR1L = 0;
        TMR1H = 0;
        T1CON.TMR1ON = 1;
    }
}
//*******************Funções****************************************************
void I2C_Start(void){                             // Essa função inicializa a start condition no barramento I2C
    SSPCON2.SEN = 1;                              // Start condition
    while(!PIR1.SSPIF);                           // Espera o fim da start condition
    PIR1.SSPIF = 0;
}

void I2C_Write(unsigned char i2c_byte){          // Transmite dados pela I2C
    SSPBUF = i2c_byte;                           // Dados para transmitir
    while(!PIR1.SSPIF);                          // Espera o fim da transmissão
    PIR1.SSPIF = 0;
}

void I2C_Repeated_Start(void){                   // Sinal I2C repeated start
    SSPCON2.RSEN = 1;                            // Repeated start condition
    while(!PIR1.SSPIF);                          // Espera o fim da start condition
    PIR1.SSPIF = 0;
}

void I2C_Stop(void){                             // Essa função inicializa a stop condition no barramento I2C
    SSPCON2.PEN = 1;                             // Stop condition
    while(!PIR1.SSPIF);                          // Espera o fim da stop condition
    PIR1.SSPIF = 0;
}

unsigned char I2C_Read(unsigned char master_ack){            // Função para a leitura da I2C e envio do bit ACK
    SSPCON2.RCEN = 1;                                        // Habilita recepção no master Mode
    while(!PIR1.SSPIF);                                      // Espera o fim da recepção
    PIR1.SSPIF = 0;
    SSPCON2.ACKDT = master_ack;
    SSPCON2.ACKEN = 1;                                       // Inicia o envio do bit ack do master para o slave
    while(!PIR1.SSPIF);                                      // Espera o fim do ack
    PIR1.SSPIF = 0;
    return SSPBUF;
}

void EUSART_write_char(unsigned char msg){     // Essa função envia um único byte pela serial EUSART
    while(!PIR1.TXIF);                         // Espera o buffer de transmissão esvaziar (Se ele estiver cheio)
    TXREG = msg;
}