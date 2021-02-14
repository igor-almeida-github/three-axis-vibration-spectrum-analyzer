
_main:

;tcc.c,13 :: 		void main() {
;tcc.c,15 :: 		int  ACCEL_XOUT=0, ACCEL_YOUT=0, ACCEL_ZOUT=0;
	CLRF       main_ACCEL_XOUT_L0+0
	CLRF       main_ACCEL_XOUT_L0+1
	CLRF       main_ACCEL_YOUT_L0+0
	CLRF       main_ACCEL_YOUT_L0+1
	CLRF       main_ACCEL_ZOUT_L0+0
	CLRF       main_ACCEL_ZOUT_L0+1
;tcc.c,17 :: 		ANSEL = 0x00;                                                               // Todas as portas são digitais AN0 até AN7
	CLRF       ANSEL+0
;tcc.c,18 :: 		ANSELH = 0x00;                                                              // Todas as portas são digitais AN8 até AN13
	CLRF       ANSELH+0
;tcc.c,19 :: 		TRISA = 0xFF;                                                               // Todas as IOs do PORTA são input
	MOVLW      255
	MOVWF      TRISA+0
;tcc.c,20 :: 		TRISB = 0xFF;                                                               // Todas as IOs do PORTB são input
	MOVLW      255
	MOVWF      TRISB+0
;tcc.c,21 :: 		TRISC = 0xFF;                                                               // Todas as IOs do PORTC são input
	MOVLW      255
	MOVWF      TRISC+0
;tcc.c,22 :: 		TRISE = 0xFF;                                                               // Todas as IOs do PORTE são input
	MOVLW      255
	MOVWF      TRISE+0
;tcc.c,25 :: 		BAUDCTL.BRG16=1;
	BSF        BAUDCTL+0, 3
;tcc.c,26 :: 		SPBRGH=0x00;
	CLRF       SPBRGH+0
;tcc.c,27 :: 		SPBRG=0x21;                                // Baud rate de 115200
	MOVLW      33
	MOVWF      SPBRG+0
;tcc.c,28 :: 		RCSTA=0x90;                                // Serial port habilitado, recepção de 8 bits, habilita recepção.
	MOVLW      144
	MOVWF      RCSTA+0
;tcc.c,29 :: 		TXSTA=0x24;                                // Modo de transmissão de 8 bits, eusart no modo assíncrono, high speed baud rate, habilita transmissão.
	MOVLW      36
	MOVWF      TXSTA+0
;tcc.c,32 :: 		SSPSTAT=0x00;                                                               // Controle da taxa de varredura para modo de alta velocidade (400kz)
	CLRF       SSPSTAT+0
;tcc.c,33 :: 		SSPCON=0x28;                                                                // Habilita MSSP no modo master clock = Fosc/(4*(SSPADD+1))
	MOVLW      40
	MOVWF      SSPCON+0
;tcc.c,34 :: 		SSPCON2=0x00;                                                               // Não inicia nada ainda, permance em idle state
	CLRF       SSPCON2+0
;tcc.c,35 :: 		SSPADD = 0x09;                                                              // I2C 400khz
	MOVLW      9
	MOVWF      SSPADD+0
;tcc.c,38 :: 		T1CON = 0x00;                                                               // Clock interno, prescale de 1, timer desligado.
	CLRF       T1CON+0
;tcc.c,39 :: 		delay_ms(200);
	MOVLW      5
	MOVWF      R11+0
	MOVLW      15
	MOVWF      R12+0
	MOVLW      241
	MOVWF      R13+0
L_main0:
	DECFSZ     R13+0, 1
	GOTO       L_main0
	DECFSZ     R12+0, 1
	GOTO       L_main0
	DECFSZ     R11+0, 1
	GOTO       L_main0
;tcc.c,41 :: 		T1CON.TMR1ON = 1;                                                           // Inicia o timer 1
	BSF        T1CON+0, 0
;tcc.c,43 :: 		for(;;){
L_main1:
;tcc.c,46 :: 		I2C_Start();
	CALL       _I2C_Start+0
;tcc.c,48 :: 		I2C_Write((MPU_Addr<<1)|0);                                             // Endereço do mpu + bit W
	MOVLW      208
	MOVWF      FARG_I2C_Write_i2c_byte+0
	CALL       _I2C_Write+0
;tcc.c,49 :: 		while(SSPCON2.ACKSTAT){                                                 // Equanto slave não acknowledge
L_main4:
	BTFSS      SSPCON2+0, 6
	GOTO       L_main5
;tcc.c,50 :: 		if (PIR1.TMR1IF){                                                   // Se o timer 1 der overflow
	BTFSS      PIR1+0, 0
	GOTO       L_main6
;tcc.c,51 :: 		PIR1.TMR1IF = 0;                                                // Reseta a flag do timer 1
	BCF        PIR1+0, 0
;tcc.c,52 :: 		I2C_Write((MPU_Addr<<1)|0);                                     // Endereço do mpu + bit W
	MOVLW      208
	MOVWF      FARG_I2C_Write_i2c_byte+0
	CALL       _I2C_Write+0
;tcc.c,53 :: 		}
L_main6:
;tcc.c,54 :: 		}
	GOTO       L_main4
L_main5:
;tcc.c,55 :: 		I2C_Write(0x3B);                                                        // ACCEL_XOUT_H: endereço do registro do MPU a ser lido primeiro
	MOVLW      59
	MOVWF      FARG_I2C_Write_i2c_byte+0
	CALL       _I2C_Write+0
;tcc.c,56 :: 		I2C_Repeated_Start();                                                   // Sinal I2C repeated start
	CALL       _I2C_Repeated_Start+0
;tcc.c,57 :: 		I2C_Write((MPU_Addr<<1)|1);                                             // Envia o endereço do MPU +  R
	MOVLW      209
	MOVWF      FARG_I2C_Write_i2c_byte+0
	CALL       _I2C_Write+0
;tcc.c,59 :: 		ACCEL_XOUT=I2C_Read(0)<<8;                                              // Lê ACCEL_XOUT_H e ACCEL_XOUT_L, envia acknowledge bit
	CLRF       FARG_I2C_Read_master_ack+0
	CALL       _I2C_Read+0
	MOVF       R0+0, 0
	MOVWF      main_ACCEL_XOUT_L0+1
	CLRF       main_ACCEL_XOUT_L0+0
;tcc.c,60 :: 		ACCEL_XOUT+=I2C_Read(0);
	CLRF       FARG_I2C_Read_master_ack+0
	CALL       _I2C_Read+0
	MOVF       R0+0, 0
	ADDWF      main_ACCEL_XOUT_L0+0, 1
	BTFSC      STATUS+0, 0
	INCF       main_ACCEL_XOUT_L0+1, 1
;tcc.c,61 :: 		EUSART_write_char(*((unsigned char*)&ACCEL_XOUT+1));                    // Envia ACCEL_XOUT_H e ACCEL_XOUT_L pela serial
	MOVF       main_ACCEL_XOUT_L0+1, 0
	MOVWF      FARG_EUSART_write_char_msg+0
	CALL       _EUSART_write_char+0
;tcc.c,62 :: 		EUSART_write_char(*((unsigned char*)&ACCEL_XOUT));
	MOVF       main_ACCEL_XOUT_L0+0, 0
	MOVWF      FARG_EUSART_write_char_msg+0
	CALL       _EUSART_write_char+0
;tcc.c,64 :: 		ACCEL_YOUT=I2C_Read(0)<<8;                                              // Lê ACCEL_YOUT_H e ACCEL_YOUT_L, envia acknowledge bit
	CLRF       FARG_I2C_Read_master_ack+0
	CALL       _I2C_Read+0
	MOVF       R0+0, 0
	MOVWF      main_ACCEL_YOUT_L0+1
	CLRF       main_ACCEL_YOUT_L0+0
;tcc.c,65 :: 		ACCEL_YOUT+=I2C_Read(0);
	CLRF       FARG_I2C_Read_master_ack+0
	CALL       _I2C_Read+0
	MOVF       R0+0, 0
	ADDWF      main_ACCEL_YOUT_L0+0, 1
	BTFSC      STATUS+0, 0
	INCF       main_ACCEL_YOUT_L0+1, 1
;tcc.c,66 :: 		EUSART_write_char(*((unsigned char*)&ACCEL_YOUT+1));                    // Envia ACCEL_YOUT_H e ACCEL_YOUT_L pela serial
	MOVF       main_ACCEL_YOUT_L0+1, 0
	MOVWF      FARG_EUSART_write_char_msg+0
	CALL       _EUSART_write_char+0
;tcc.c,67 :: 		EUSART_write_char(*((unsigned char*)&ACCEL_YOUT));
	MOVF       main_ACCEL_YOUT_L0+0, 0
	MOVWF      FARG_EUSART_write_char_msg+0
	CALL       _EUSART_write_char+0
;tcc.c,69 :: 		ACCEL_ZOUT=I2C_Read(0)<<8;                                              // Lê ACCEL_ZOUT_H e ACCEL_ZOUT_L, envia NOT acknowledge bit
	CLRF       FARG_I2C_Read_master_ack+0
	CALL       _I2C_Read+0
	MOVF       R0+0, 0
	MOVWF      main_ACCEL_ZOUT_L0+1
	CLRF       main_ACCEL_ZOUT_L0+0
;tcc.c,70 :: 		ACCEL_ZOUT+=I2C_Read(1);
	MOVLW      1
	MOVWF      FARG_I2C_Read_master_ack+0
	CALL       _I2C_Read+0
	MOVF       R0+0, 0
	ADDWF      main_ACCEL_ZOUT_L0+0, 1
	BTFSC      STATUS+0, 0
	INCF       main_ACCEL_ZOUT_L0+1, 1
;tcc.c,71 :: 		EUSART_write_char(*((unsigned char*)&ACCEL_ZOUT+1));                    // Envia ACCEL_ZOUT_H e ACCEL_ZOUT_L pela serial
	MOVF       main_ACCEL_ZOUT_L0+1, 0
	MOVWF      FARG_EUSART_write_char_msg+0
	CALL       _EUSART_write_char+0
;tcc.c,72 :: 		EUSART_write_char(*((unsigned char*)&ACCEL_ZOUT));
	MOVF       main_ACCEL_ZOUT_L0+0, 0
	MOVWF      FARG_EUSART_write_char_msg+0
	CALL       _EUSART_write_char+0
;tcc.c,74 :: 		I2C_Stop();
	CALL       _I2C_Stop+0
;tcc.c,76 :: 		EUSART_write_char(*((unsigned char*)&timer+1));                         // Envia tempo pela serial
	MOVF       main_timer_L0+1, 0
	MOVWF      FARG_EUSART_write_char_msg+0
	CALL       _EUSART_write_char+0
;tcc.c,77 :: 		EUSART_write_char(*((unsigned char*)&timer));
	MOVF       main_timer_L0+0, 0
	MOVWF      FARG_EUSART_write_char_msg+0
	CALL       _EUSART_write_char+0
;tcc.c,79 :: 		EUSART_write_char(0x0D);                                                // CR
	MOVLW      13
	MOVWF      FARG_EUSART_write_char_msg+0
	CALL       _EUSART_write_char+0
;tcc.c,80 :: 		EUSART_write_char(0x0A);                                                // Nova linha LF(Line feed))
	MOVLW      10
	MOVWF      FARG_EUSART_write_char_msg+0
	CALL       _EUSART_write_char+0
;tcc.c,82 :: 		T1CON.TMR1ON = 0;
	BCF        T1CON+0, 0
;tcc.c,83 :: 		timer = TMR1L + (TMR1H<<8);
	MOVF       TMR1H+0, 0
	MOVWF      R0+1
	CLRF       R0+0
	MOVF       R0+0, 0
	ADDWF      TMR1L+0, 0
	MOVWF      main_timer_L0+0
	MOVLW      0
	BTFSC      STATUS+0, 0
	ADDLW      1
	ADDWF      R0+1, 0
	MOVWF      main_timer_L0+1
;tcc.c,84 :: 		TMR1L = 0;
	CLRF       TMR1L+0
;tcc.c,85 :: 		TMR1H = 0;
	CLRF       TMR1H+0
;tcc.c,86 :: 		T1CON.TMR1ON = 1;
	BSF        T1CON+0, 0
;tcc.c,87 :: 		}
	GOTO       L_main1
;tcc.c,88 :: 		}
L_end_main:
	GOTO       $+0
; end of _main

_I2C_Start:

;tcc.c,90 :: 		void I2C_Start(void){                             // Essa função inicializa a start condition no barramento I2C
;tcc.c,91 :: 		SSPCON2.SEN = 1;                              // Start condition
	BSF        SSPCON2+0, 0
;tcc.c,92 :: 		while(!PIR1.SSPIF);                           // Espera o fim da start condition
L_I2C_Start7:
	BTFSC      PIR1+0, 3
	GOTO       L_I2C_Start8
	GOTO       L_I2C_Start7
L_I2C_Start8:
;tcc.c,93 :: 		PIR1.SSPIF = 0;
	BCF        PIR1+0, 3
;tcc.c,94 :: 		}
L_end_I2C_Start:
	RETURN
; end of _I2C_Start

_I2C_Write:

;tcc.c,96 :: 		void I2C_Write(unsigned char i2c_byte){          // Transmite dados pela I2C
;tcc.c,97 :: 		SSPBUF = i2c_byte;                           // Dados para transmitir
	MOVF       FARG_I2C_Write_i2c_byte+0, 0
	MOVWF      SSPBUF+0
;tcc.c,98 :: 		while(!PIR1.SSPIF);                          // Espera o fim da transmissão
L_I2C_Write9:
	BTFSC      PIR1+0, 3
	GOTO       L_I2C_Write10
	GOTO       L_I2C_Write9
L_I2C_Write10:
;tcc.c,99 :: 		PIR1.SSPIF = 0;
	BCF        PIR1+0, 3
;tcc.c,100 :: 		}
L_end_I2C_Write:
	RETURN
; end of _I2C_Write

_I2C_Repeated_Start:

;tcc.c,102 :: 		void I2C_Repeated_Start(void){                   // Sinal I2C repeated start
;tcc.c,103 :: 		SSPCON2.RSEN = 1;                            // Repeated start condition
	BSF        SSPCON2+0, 1
;tcc.c,104 :: 		while(!PIR1.SSPIF);                          // Espera o fim da start condition
L_I2C_Repeated_Start11:
	BTFSC      PIR1+0, 3
	GOTO       L_I2C_Repeated_Start12
	GOTO       L_I2C_Repeated_Start11
L_I2C_Repeated_Start12:
;tcc.c,105 :: 		PIR1.SSPIF = 0;
	BCF        PIR1+0, 3
;tcc.c,106 :: 		}
L_end_I2C_Repeated_Start:
	RETURN
; end of _I2C_Repeated_Start

_I2C_Stop:

;tcc.c,108 :: 		void I2C_Stop(void){                             // Essa função inicializa a stop condition no barramento I2C
;tcc.c,109 :: 		SSPCON2.PEN = 1;                             // Stop condition
	BSF        SSPCON2+0, 2
;tcc.c,110 :: 		while(!PIR1.SSPIF);                          // Espera o fim da stop condition
L_I2C_Stop13:
	BTFSC      PIR1+0, 3
	GOTO       L_I2C_Stop14
	GOTO       L_I2C_Stop13
L_I2C_Stop14:
;tcc.c,111 :: 		PIR1.SSPIF = 0;
	BCF        PIR1+0, 3
;tcc.c,112 :: 		}
L_end_I2C_Stop:
	RETURN
; end of _I2C_Stop

_I2C_Read:

;tcc.c,114 :: 		unsigned char I2C_Read(unsigned char master_ack){            // Função para a leitura da I2C e envio do bit ACK
;tcc.c,115 :: 		SSPCON2.RCEN = 1;                                        // Habilita recepção no master Mode
	BSF        SSPCON2+0, 3
;tcc.c,116 :: 		while(!PIR1.SSPIF);                                      // Espera o fim da recepção
L_I2C_Read15:
	BTFSC      PIR1+0, 3
	GOTO       L_I2C_Read16
	GOTO       L_I2C_Read15
L_I2C_Read16:
;tcc.c,117 :: 		PIR1.SSPIF = 0;
	BCF        PIR1+0, 3
;tcc.c,118 :: 		SSPCON2.ACKDT = master_ack;
	BTFSC      FARG_I2C_Read_master_ack+0, 0
	GOTO       L__I2C_Read27
	BCF        SSPCON2+0, 5
	GOTO       L__I2C_Read28
L__I2C_Read27:
	BSF        SSPCON2+0, 5
L__I2C_Read28:
;tcc.c,119 :: 		SSPCON2.ACKEN = 1;                                       // Inicia o envio do bit ack do master para o slave
	BSF        SSPCON2+0, 4
;tcc.c,120 :: 		while(!PIR1.SSPIF);                                      // Espera o fim do ack
L_I2C_Read17:
	BTFSC      PIR1+0, 3
	GOTO       L_I2C_Read18
	GOTO       L_I2C_Read17
L_I2C_Read18:
;tcc.c,121 :: 		PIR1.SSPIF = 0;
	BCF        PIR1+0, 3
;tcc.c,122 :: 		return SSPBUF;
	MOVF       SSPBUF+0, 0
	MOVWF      R0+0
;tcc.c,123 :: 		}
L_end_I2C_Read:
	RETURN
; end of _I2C_Read

_EUSART_write_char:

;tcc.c,125 :: 		void EUSART_write_char(unsigned char msg){     // Essa função envia um único byte pela serial EUSART
;tcc.c,126 :: 		while(!PIR1.TXIF);                         // Espera o buffer de transmissão esvaziar (Se ele estiver cheio)
L_EUSART_write_char19:
	BTFSC      PIR1+0, 4
	GOTO       L_EUSART_write_char20
	GOTO       L_EUSART_write_char19
L_EUSART_write_char20:
;tcc.c,127 :: 		TXREG = msg;
	MOVF       FARG_EUSART_write_char_msg+0, 0
	MOVWF      TXREG+0
;tcc.c,128 :: 		}
L_end_EUSART_write_char:
	RETURN
; end of _EUSART_write_char
