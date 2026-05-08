#include <stdio.h>
#include <pthread.h>

#ifndef __RFT_UART_H__
#define __RFT_UART_H__

typedef int BOOL;
#define TRUE 1
#define FALSE 0

#define txbuff_size (100)
#define rxbuff_size (4096) // 1024*4
#define txPacket_size (11) // 1(SOP) + 8(DATA) + 1(CHECKSUM) + 1(EOP)
#define rxPacket_size (19) // 1(SOP) + 16(DATA) + 1(CHECKSUM) + 1(EOP)

class PROGRAM
{
public:
    int linux_getch(void);

};


class RFT_UART
{
public:
    BOOL openPort( char* devname, int portnum, unsigned long buad, unsigned long byte_size );
    BOOL closePort(void);
    BOOL setDivider(float g_force_divider, float g_torque_divider);
    BOOL sendPacket(void);
    BOOL rcvPacket(void);

    unsigned char txbuff[txbuff_size];
    unsigned char rxbuff[rxbuff_size];
    unsigned char txPacket[txPacket_size];
    unsigned char rxPacket[rxPacket_size];

    unsigned char calcChecksum(unsigned char* pkt_buff, int pkt_size);
    
    void convertPacket_To_Force(unsigned char* rxPacket);

    float force[6];

protected:
    float force_divider;
    float torque_divider;
    BOOL        portConnected = FALSE;  // Open/Closed indicating flag
    BOOL command_on = FALSE;            // Command On/Off flag
    BOOL data_processed_check = FALSE;  // data processed check
private:

    int fd;
    pthread_t Thread1;

};

#endif//__RFT_UART_H__