/*
    2023-11-23 Seunghoon Kang | Soft Robotics & Bionics Lab
    Copyright (C) 2023 by SRBL, Seoul National University. All rights reserved.
*/
#include <stdio.h>
#include <iostream>
#include <unistd.h> // Linux
#include <termios.h>
#include <fcntl.h>
#include <sys/types.h>
#include <sys/stat.h>
#include <string.h>

#include "RFT_UART.h" // RFT_UART sensor

#define portnum (0)

#define SOP 0x55
#define EOP 0xAA

unsigned long buad = B921600;
unsigned long byte_size = CS8;

float		g_force_divider 	= 50.0f;    // for more information to refer the RFT sensor manual
float		g_torque_divider 	= 2000.0f;  // for more information to refer the RFT sensor manual

float g_force[6]; // GLOBAL VARIABLE


/* ROS */
#include "rclcpp/rclcpp.hpp"
#include "std_msgs/msg/float32_multi_array.hpp"

using namespace std::chrono_literals;

class SensorRFT_Publisher : public rclcpp::Node
{
public:
    SensorRFT_Publisher() : Node("sensorRFT_publisher")
    {
        publisher_ = this->create_publisher<std_msgs::msg::Float32MultiArray>("sensorRFT", 10);

        // Publish the float array every 1 milli second
        timer_ = this->create_wall_timer(
            1ms, std::bind(&SensorRFT_Publisher::timerCallback, this));
    }

private:
    void timerCallback()
    {
        auto message = std_msgs::msg::Float32MultiArray();
        message.layout.dim.push_back(std_msgs::msg::MultiArrayDimension());
        message.layout.dim[0].size = 6; // Size of the array
        message.layout.dim[0].stride = 1; // Stride is 1 because it's a 1D array
        message.layout.dim[0].label = "float_array";

        // Populate the float array
        message.data = {g_force[0], g_force[1], g_force[2],
                        g_force[3], g_force[4], g_force[5],};

        // log
        // RCLCPP_INFO(this->get_logger(), "[%5.3f, %5.3f, %5.3f, %5.3f, %5.3f, %5.3f]",
        //             message.data[0], message.data[1], message.data[2],
        //             message.data[3], message.data[4], message.data[5]);
        publisher_->publish(message);
    }

    rclcpp::Publisher<std_msgs::msg::Float32MultiArray>::SharedPtr publisher_;
    rclcpp::TimerBase::SharedPtr timer_;

};// class SensorT_Publisher


////////////////////////////////////////////

void *p_function(void * pSerial)
{
	( (RFT_UART *)pSerial )->rcvPacket();

	return NULL;
};

////////////////////////////////////////////

BOOL RFT_UART::openPort( char* devname, int m_portnum, unsigned long buad, unsigned long byte_size )
{
    char port[20];
    sprintf(port,"%s%d", devname, m_portnum);
    printf("port is opening...");
    fd = open(port, O_RDWR | O_NOCTTY | O_NDELAY );
    if (fd == -1 )
    {
        printf("cannot open the serial port");
        return FALSE;
    }
    printf("we opened serial port: %s\n", port);
    
    portConnected = TRUE;
    
    usleep(350);

    // port setting
    struct termios oldtio, newtio;

	tcgetattr(fd,&oldtio); /* save current serial port settings */
	bzero(&newtio, sizeof(newtio)); /* clear struct for new port settings */

	newtio.c_cflag = buad | byte_size | CLOCAL | CREAD;
	tcsetattr(fd,TCSANOW,&newtio);

    /* THREAD */
    int result = pthread_create( &Thread1, NULL, p_function, (void *)this );
	if( result != 0 ) 
	{
		printf("\nCan't create read thread");
		closePort();
	}
    else
        printf("THREAD YES\n");

    return TRUE;
}

BOOL RFT_UART::closePort(void)
{
    close(fd);
    portConnected = FALSE; // flag
    return TRUE;
}

BOOL RFT_UART::setDivider(float g_force_divider, float g_torque_divider)
{
    force_divider = g_force_divider;
    torque_divider = g_torque_divider;
    return TRUE;
}

BOOL RFT_UART::sendPacket(void)
{   
    
    //while( portConnected )
    //{
        int n_byte_temp = 0;
        memset(txPacket, 0x00, txPacket_size * sizeof(char));
        
        // Set Bias : ON
        unsigned char txPacket_temp_b[] = {SOP,0x11,0x01,0x00,0x00,0x00,0x00,0x00,0x00,0x12,EOP};
        std::memcpy(txPacket, txPacket_temp_b, sizeof(txPacket));
        do{
            int n_byte = write(fd, txPacket, sizeof(txPacket));
            n_byte_temp = n_byte;
            printf("\nwrite: %d bytes\n",n_byte_temp);
            usleep(100);
        }while( n_byte_temp < (int)sizeof(txPacket)); // 11
        usleep(500000);

        // Set Baud-rate : 921,600 bps
        unsigned char txPacket_temp_B[] = {SOP,0x06,0x01,0x00,0x00,0x00,0x00,0x00,0x00,0x07,EOP};
        std::memcpy(txPacket, txPacket_temp_B, sizeof(txPacket));
        do{
            int n_byte = write(fd, txPacket, sizeof(txPacket));
            n_byte_temp = n_byte;
            printf("\nwrite: %d bytes\n",n_byte_temp);
            usleep(100);
        }while( n_byte_temp < (int)sizeof(txPacket)); // 11
        usleep(500000);

        // Set Data Output Rate : 1000Hz
        unsigned char txPacket_temp_r[] = {SOP,0x0F,0x08,0x00,0x00,0x00,0x00,0x00,0x00,0x17,EOP};
        std::memcpy(txPacket, txPacket_temp_r, sizeof(txPacket));
        do{
            int n_byte = write(fd, txPacket, sizeof(txPacket));
            n_byte_temp = n_byte;
            printf("\nwrite: %d bytes\n",n_byte_temp);
            usleep(100);
        }while( n_byte_temp < (int)sizeof(txPacket)); // 11
        usleep(500000);

        // No Filter
        // START F/T DATA OUTPUT
        txPacket[0] = SOP; // SOP 0x55
        txPacket[1] = 0x0B; // START F/T DATA OUTPUT
        txPacket[txPacket_size-2] = calcChecksum(txPacket, txPacket_size);
        txPacket[txPacket_size-1] = EOP; // EOP 0xAA
        do{
            int n_byte = write(fd, txPacket, sizeof(txPacket));
            n_byte_temp = n_byte;
            printf("\nwrite: %d bytes\n",n_byte_temp);
            usleep(100);
        }while( n_byte_temp < (int)sizeof(txPacket)); // 11
        printf("send packet yes\n");
        command_on = TRUE;
    //}

    return TRUE;
}

BOOL RFT_UART::rcvPacket(void)
{
    memset(rxbuff, 0x00, rxbuff_size * sizeof(char));
    memset(rxPacket, 0x00, rxPacket_size * sizeof(char));
    int rxbuff_index = 0;
    //unsigned char rxbuff_temp[1024*2] = { };
    #define BUFF_SIZE 1024
    char 	   buff[BUFF_SIZE];

    while( portConnected )
    {   
        // check command
        if (!command_on )
        {
            // printf("\ngive me command");
            sleep(1);
            continue;
        }

        int n_byte = read(fd, buff, BUFF_SIZE);
		if( n_byte <= 0 )
		{
			//usleep( 1000 ); // just sleep.
			continue;
		}  

		// data copy
		for( int i = 0; i < n_byte; i++)
		{
			rxbuff[rxbuff_index + i] = buff[i];
		}
		rxbuff_index += n_byte;

		// wait packet.... 
		if (rxbuff_index < rxPacket_size)
		{
			printf("RECEIVED: %d\n", rxbuff_index);
			continue;
		}

		// find SOP
		int found_idx = -1;
		for (int i = 0; i < rxbuff_index; i++)
		{
			if (rxbuff[i] == 0x55) // SOP
			{
				found_idx = i;      // usually 1~10
				break;
			}
		}

		if (found_idx == -1)
		{
			rxbuff_index = 0;
			printf("SOP NOT FOUNDED\n");
			continue;
		}
		// if the index of SOP is not first(0), shift received data....
		if (found_idx != 0) 
		{
			for (int i = 0; i < (rxbuff_index - found_idx); i++)
			{
				rxbuff[i] = rxbuff[i + found_idx];
			}
			printf("SHIFT\n");
			rxbuff_index = rxbuff_index - found_idx;
		}
        //printf("%d\n", rxbuff_index);

		// packet handling....
		if (rxbuff_index >= rxPacket_size )
        {
            // transfer 
            int pkt_size = rxPacket_size;
            int num_of_rxPkt = rxbuff_index / pkt_size;
            int num_of_next_byte = rxbuff_index % pkt_size;
            int transfer_data_size;
            int restart_idx;
            // if the number of received packet is more than 1, 
            // move the last packet data to first location of buffer to interprete the last received data.
            if (num_of_rxPkt > 1) 
            {
                transfer_data_size = pkt_size + num_of_next_byte;
                restart_idx = (num_of_rxPkt - 1) * pkt_size;

                for (int i = 0; i < transfer_data_size; i++)
                    rxbuff[i] = rxbuff[restart_idx + i];

                //printf("DATA TRANSFER - BEFORE\n");
            }
 
            if (num_of_rxPkt >= 1 )
            {
                for ( int i = 0; i < rxPacket_size; i++)
                {
                    rxPacket[i] = rxbuff[i];
                }
                //if ( rxPacket == 0)
                    //continue; //break;

                unsigned char checksum = calcChecksum(rxPacket, rxPacket_size);
                if ((rxPacket[0] == 0x55) // SOP
                    && (rxPacket[rxPacket_size - 2] == checksum)
                    && (rxPacket[rxPacket_size - 1] == 0xAA)) // EOP
                {
                    //printf("RIGHT");
                    //sleep(2);
                    convertPacket_To_Force(rxPacket);
                }
                else
                    printf("WRONG");
                    //continue; //break;

                if( data_processed_check )
                {
                    if (num_of_next_byte)
                    {
                        transfer_data_size = num_of_next_byte;
                        restart_idx = pkt_size;
                        for (int i = 0; i < transfer_data_size; i++)
                            rxbuff[i] = rxbuff[restart_idx + i];

                        //printf("DATA TRANSFER - AFTER\n");

                        rxbuff_index = num_of_next_byte;
                    }
                    else
                    {
                        rxbuff_index = 0; 
                    }

                }
            }
        }
    }
    return TRUE;
}

void RFT_UART::convertPacket_To_Force(unsigned char* rxPacket)
{
    short raw; // rxPacket_size - 3 = 16
    unsigned short temp;

    for (int i = 0; i < 6; i++)
    {
        temp = rxPacket[2 + i*2]*256 + rxPacket[3 + i*2];
        raw = (signed short)temp;
        
        if( i < 3 )
        {
            // force
            force[i] = ((float)raw) / force_divider;
            g_force[i] = force[i]; // GLOBAL VARIABLE
        }
        else
        {   
            // torque
            force[i] = ((float)raw) / torque_divider;
            g_force[i] = force[i]; // GLOBAL VARIABLE
        }
    }

    // printf("%5.3f %5.3f %5.3f %5.3f %5.3f %5.3f\n", force[0], force[1], force[2], force[3], force[4], force[5]);
    
    data_processed_check = TRUE;
}



// functions for UART communication, checksum calculation, UART Packet generation
unsigned char RFT_UART::calcChecksum(unsigned char *pkt_buff, int pkt_size)
{
	unsigned char checksum = 0;

	for (int idx = 1; idx < (pkt_size - 2); idx++) // except SOP, CHECKSUM and EOP
		checksum += pkt_buff[idx];

	return checksum;
}



//////////////////////////////////////////////////////////////
//////////////////////////////////////////////////////////////
//////////////////////////////////////////////////////////////


// class variable
RFT_UART RFT_SENSOR;

int main(int argc, char *argv[])
{

	// bool isGo = true;

	char devName[] = "/dev/ttyUSB";

	printf("RFT TEST SOFWARE\n");

	RFT_SENSOR.openPort( devName, portnum, buad, byte_size );
	// initialize force/torque divider
	RFT_SENSOR.setDivider(g_force_divider, g_torque_divider); // V1.1
	usleep(1000000);  // 1 second

	RFT_SENSOR.sendPacket();

    // ROS2
    rclcpp::init(argc, argv);
    auto node = std::make_shared<SensorRFT_Publisher>();
    rclcpp::spin(node);
    rclcpp::shutdown();
	
	RFT_SENSOR.closePort();
	
	return 0;
}

///////////////////////
// End of This File






