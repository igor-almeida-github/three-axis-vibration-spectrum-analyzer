#line 1 "C:/Users/igor_/Documents/Microcontroladores/PIC/Mikroc/TCC/tcc.c"



void I2C_Start(void);
void I2C_Write(unsigned char i2c_byte);
void I2C_Repeated_Start(void);
void I2C_Stop(void);
unsigned char I2C_Read(unsigned char master_ack);
void EUSART_init(void);
void EUSART_write_char(unsigned char msg);
void EUSART_write_text(unsigned char*string);

void main() {

 int ACCEL_XOUT=0, ACCEL_YOUT=0, ACCEL_ZOUT=0;
 unsigned int timer;
 ANSEL = 0x00;
 ANSELH = 0x00;
 TRISA = 0xFF;
 TRISB = 0xFF;
 TRISC = 0xFF;
 TRISE = 0xFF;


 BAUDCTL.BRG16=1;
 SPBRGH=0x00;
 SPBRG=0x21;
 RCSTA=0x90;
 TXSTA=0x24;


 SSPSTAT=0x00;
 SSPCON=0x28;
 SSPCON2=0x00;
 SSPADD = 0x09;


 T1CON = 0x00;
 delay_ms(200);

 T1CON.TMR1ON = 1;

 for(;;){


 I2C_Start();

 I2C_Write(( 0x68 <<1)|0);
 while(SSPCON2.ACKSTAT){
 if (PIR1.TMR1IF){
 PIR1.TMR1IF = 0;
 I2C_Write(( 0x68 <<1)|0);
 }
 }
 I2C_Write(0x3B);
 I2C_Repeated_Start();
 I2C_Write(( 0x68 <<1)|1);

 ACCEL_XOUT=I2C_Read(0)<<8;
 ACCEL_XOUT+=I2C_Read(0);
 EUSART_write_char(*((unsigned char*)&ACCEL_XOUT+1));
 EUSART_write_char(*((unsigned char*)&ACCEL_XOUT));

 ACCEL_YOUT=I2C_Read(0)<<8;
 ACCEL_YOUT+=I2C_Read(0);
 EUSART_write_char(*((unsigned char*)&ACCEL_YOUT+1));
 EUSART_write_char(*((unsigned char*)&ACCEL_YOUT));

 ACCEL_ZOUT=I2C_Read(0)<<8;
 ACCEL_ZOUT+=I2C_Read(1);
 EUSART_write_char(*((unsigned char*)&ACCEL_ZOUT+1));
 EUSART_write_char(*((unsigned char*)&ACCEL_ZOUT));

 I2C_Stop();

 EUSART_write_char(*((unsigned char*)&timer+1));
 EUSART_write_char(*((unsigned char*)&timer));

 EUSART_write_char(0x0D);
 EUSART_write_char(0x0A);

 T1CON.TMR1ON = 0;
 timer = TMR1L + (TMR1H<<8);
 TMR1L = 0;
 TMR1H = 0;
 T1CON.TMR1ON = 1;
 }
}

void I2C_Start(void){
 SSPCON2.SEN = 1;
 while(!PIR1.SSPIF);
 PIR1.SSPIF = 0;
}

void I2C_Write(unsigned char i2c_byte){
 SSPBUF = i2c_byte;
 while(!PIR1.SSPIF);
 PIR1.SSPIF = 0;
}

void I2C_Repeated_Start(void){
 SSPCON2.RSEN = 1;
 while(!PIR1.SSPIF);
 PIR1.SSPIF = 0;
}

void I2C_Stop(void){
 SSPCON2.PEN = 1;
 while(!PIR1.SSPIF);
 PIR1.SSPIF = 0;
}

unsigned char I2C_Read(unsigned char master_ack){
 SSPCON2.RCEN = 1;
 while(!PIR1.SSPIF);
 PIR1.SSPIF = 0;
 SSPCON2.ACKDT = master_ack;
 SSPCON2.ACKEN = 1;
 while(!PIR1.SSPIF);
 PIR1.SSPIF = 0;
 return SSPBUF;
}

void EUSART_write_char(unsigned char msg){
 while(!PIR1.TXIF);
 TXREG = msg;
}
