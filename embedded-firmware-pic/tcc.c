#define MPU_Addr 0x68

//*****************Prot�tipos_de_fun��es****************************************
void I2C_Start(void);                                                           // Essa fun��o inicializa a start condition no barramento I2C
void I2C_Write(unsigned char i2c_byte);                                         // Transmite dados pela I2C
void I2C_Repeated_Start(void);                                                  // Sinal I2C repeated start
void I2C_Stop(void);                                                            // Essa fun��o inicializa a stop condition no barramento I2C
unsigned char I2C_Read(unsigned char master_ack);                               // Fun��o para a leitura da I2C e envio do bit ACK
void EUSART_init(void);                                                         // Essa fun��o inicializa o m�dulo EUSART do pic16f883
void EUSART_write_char(unsigned char msg);                                      // Essa fun��o envia um �nico byte pela serial EUSART
void EUSART_write_text(unsigned char*string);                                   // Essa fun��o envia uma string de texto inteira pela eusart, at� encontrar o caracter null

void main() {
    //*************Declara��o_de_vari�veis_de_escopo_local**********************
    int  ACCEL_XOUT=0, ACCEL_YOUT=0, ACCEL_ZOUT=0;
    unsigned int timer;
    ANSEL = 0x00;                                                               // Todas as portas s�o digitais AN0 at� AN7
    ANSELH = 0x00;                                                              // Todas as portas s�o digitais AN8 at� AN13
    TRISA = 0xFF;                                                               // Todas as IOs do PORTA s�o input
    TRISB = 0xFF;                                                               // Todas as IOs do PORTB s�o input
    TRISC = 0xFF;                                                               // Todas as IOs do PORTC s�o input
    TRISE = 0xFF;                                                               // Todas as IOs do PORTE s�o input

    //*************Configura��es_EUSART*****************************************
    BAUDCTL.BRG16=1;
    SPBRGH=0x00;
    SPBRG=0x21;                                // Baud rate de 115200
    RCSTA=0x90;                                // Serial port habilitado, recep��o de 8 bits, habilita recep��o.
    TXSTA=0x24;                                // Modo de transmiss�o de 8 bits, eusart no modo ass�ncrono, high speed baud rate, habilita transmiss�o.

    //*************Configura��es_I2C********************************************
    SSPSTAT=0x00;                                                               // Controle da taxa de varredura para modo de alta velocidade (400kz)
    SSPCON=0x28;                                                                // Habilita MSSP no modo master clock = Fosc/(4*(SSPADD+1))
    SSPCON2=0x00;                                                               // N�o inicia nada ainda, permance em idle state
    SSPADD = 0x09;                                                              // I2C 400khz
    
    //*************Configura��es_timer_1****************************************
    T1CON = 0x00;                                                               // Clock interno, prescale de 1, timer desligado.
    delay_ms(200);
    
    T1CON.TMR1ON = 1;                                                           // Inicia o timer 1
    
    for(;;){
    
        //**************************Le_dados_do_MPU*****************************
        I2C_Start();
        
        I2C_Write((MPU_Addr<<1)|0);                                             // Endere�o do mpu + bit W
        while(SSPCON2.ACKSTAT){                                                 // Equanto slave n�o acknowledge
            if (PIR1.TMR1IF){                                                   // Se o timer 1 der overflow
                PIR1.TMR1IF = 0;                                                // Reseta a flag do timer 1
                I2C_Write((MPU_Addr<<1)|0);                                     // Endere�o do mpu + bit W
            }
        }
        I2C_Write(0x3B);                                                        // ACCEL_XOUT_H: endere�o do registro do MPU a ser lido primeiro
        I2C_Repeated_Start();                                                   // Sinal I2C repeated start
        I2C_Write((MPU_Addr<<1)|1);                                             // Envia o endere�o do MPU +  R

        ACCEL_XOUT=I2C_Read(0)<<8;                                              // L� ACCEL_XOUT_H e ACCEL_XOUT_L, envia acknowledge bit
        ACCEL_XOUT+=I2C_Read(0);
        EUSART_write_char(*((unsigned char*)&ACCEL_XOUT+1));                    // Envia ACCEL_XOUT_H e ACCEL_XOUT_L pela serial
        EUSART_write_char(*((unsigned char*)&ACCEL_XOUT));
        
        ACCEL_YOUT=I2C_Read(0)<<8;                                              // L� ACCEL_YOUT_H e ACCEL_YOUT_L, envia acknowledge bit
        ACCEL_YOUT+=I2C_Read(0);
        EUSART_write_char(*((unsigned char*)&ACCEL_YOUT+1));                    // Envia ACCEL_YOUT_H e ACCEL_YOUT_L pela serial
        EUSART_write_char(*((unsigned char*)&ACCEL_YOUT));
        
        ACCEL_ZOUT=I2C_Read(0)<<8;                                              // L� ACCEL_ZOUT_H e ACCEL_ZOUT_L, envia NOT acknowledge bit
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
//*******************Fun��es****************************************************
void I2C_Start(void){                             // Essa fun��o inicializa a start condition no barramento I2C
    SSPCON2.SEN = 1;                              // Start condition
    while(!PIR1.SSPIF);                           // Espera o fim da start condition
    PIR1.SSPIF = 0;
}

void I2C_Write(unsigned char i2c_byte){          // Transmite dados pela I2C
    SSPBUF = i2c_byte;                           // Dados para transmitir
    while(!PIR1.SSPIF);                          // Espera o fim da transmiss�o
    PIR1.SSPIF = 0;
}

void I2C_Repeated_Start(void){                   // Sinal I2C repeated start
    SSPCON2.RSEN = 1;                            // Repeated start condition
    while(!PIR1.SSPIF);                          // Espera o fim da start condition
    PIR1.SSPIF = 0;
}

void I2C_Stop(void){                             // Essa fun��o inicializa a stop condition no barramento I2C
    SSPCON2.PEN = 1;                             // Stop condition
    while(!PIR1.SSPIF);                          // Espera o fim da stop condition
    PIR1.SSPIF = 0;
}

unsigned char I2C_Read(unsigned char master_ack){            // Fun��o para a leitura da I2C e envio do bit ACK
    SSPCON2.RCEN = 1;                                        // Habilita recep��o no master Mode
    while(!PIR1.SSPIF);                                      // Espera o fim da recep��o
    PIR1.SSPIF = 0;
    SSPCON2.ACKDT = master_ack;
    SSPCON2.ACKEN = 1;                                       // Inicia o envio do bit ack do master para o slave
    while(!PIR1.SSPIF);                                      // Espera o fim do ack
    PIR1.SSPIF = 0;
    return SSPBUF;
}

void EUSART_write_char(unsigned char msg){     // Essa fun��o envia um �nico byte pela serial EUSART
    while(!PIR1.TXIF);                         // Espera o buffer de transmiss�o esvaziar (Se ele estiver cheio)
    TXREG = msg;
}