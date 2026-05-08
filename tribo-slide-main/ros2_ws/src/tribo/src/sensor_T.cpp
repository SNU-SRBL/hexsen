/*
    2023-11-23 Seunghoon Kang | Soft Robotics & Bionics Lab
    Copyright (C) 2023 by SRBL, Seoul National University. All rights reserved.
*/
#include <iostream>
#include <stdio.h>
#include <termios.h>
#include <unistd.h>
#include <fcntl.h>
#include <sys/types.h>
#include <sys/stat.h>
#include <string.h>

#include <sys/ioctl.h>

#include <pthread.h>
// Linux
#include <unistd.h>

typedef int BOOL;
#define TRUE 1
#define FALSE 0

#define txbuff_size (100)
#define rxbuff_size (1024) // 1024
// #define txPacket_size (11) // 1(SOP) + 8(DATA) + 1(CHECKSUM) + 1(EOP)
// #define rxPacket_size (19) // 1(SOP) + 16(DATA) + 1(CHECKSUM) + 1(EOP)

#define sensorDataNum (4) // SUDONG

#define portnum (0)
unsigned long baud = B115200;
unsigned long byte_size = CS8;

float g_sensorData[sensorDataNum]; // SUDONG // GLOBAL VARIABLE


/* ROS */
#include "rclcpp/rclcpp.hpp"
#include "std_msgs/msg/float32_multi_array.hpp"

using namespace std;
using namespace std::chrono_literals;

class SensorT_Publisher : public rclcpp::Node
{
public:
    SensorT_Publisher() : Node("sensorT_publisher")
    {
        publisher_ = this->create_publisher<std_msgs::msg::Float32MultiArray>("sensorT", 10);

        // Publish the float array every 1 milli second
        // 1ms for Data collection, 1.2ms for Inference
        timer_ = this->create_wall_timer(
            1.0ms, std::bind(&SensorT_Publisher::timerCallback, this));

        // Initialize calibration variables
        calibrated_ = false;
        calib_count_ = 0;
        for (int i = 0; i < sensorDataNum; ++i)
        {
            offset_[i] = 0.0f;
            calib_sum_[i] = 0.0f;
        }
        RCLCPP_INFO(this->get_logger(), "SensorT Publisher Node has been started. Calibrating...");
    }

private:
    static constexpr int N_CALIB = 1000;  // 500~1000 recommended

    void timerCallback()
    {
        // Calibration phase
        if (!calibrated_) {
            calib_count_++;
            for (int i = 0; i < sensorDataNum; ++i)
            {
                calib_sum_[i] += g_sensorData[i];
            }
            if (calib_count_ >= N_CALIB) // After 1000 samples
            {
                for (int i = 0; i < sensorDataNum; ++i)
                {
                    offset_[i] = calib_sum_[i] / static_cast<float>(calib_count_);
                }
                calibrated_ = true;
                RCLCPP_INFO(this->get_logger(), "Calibration completed. Offsets: [%6.2f, %6.2f, %6.2f, %6.2f]",
                            offset_[0], offset_[1], offset_[2], offset_[3]);
            }
            return; // Skip publishing during calibration
        }

        auto message = std_msgs::msg::Float32MultiArray();
        message.layout.dim.push_back(std_msgs::msg::MultiArrayDimension());
        message.layout.dim[0].size = 4; // Size of the array
        message.layout.dim[0].stride = 1; // Stride is 1 because it's a 1D array
        message.layout.dim[0].label = "float_array";

        // Populate the float array
        for (int i = 0; i < sensorDataNum; ++i){
            message.data.push_back(g_sensorData[i] - offset_[i]);
        }

        // log
        // RCLCPP_INFO(this->get_logger(), "[%6.2f, %6.2f, %6.2f, %6.2f]",
        //             message.data[0], message.data[1], message.data[2], message.data[3]);
        publisher_->publish(message);
    }

    rclcpp::Publisher<std_msgs::msg::Float32MultiArray>::SharedPtr publisher_;
    rclcpp::TimerBase::SharedPtr timer_;

    bool  calibrated_;
    int   calib_count_;
    float calib_sum_[4];
    float offset_[4];

};// class SensorT_Publisher

//////////////////////////////////////////////////////////


class SENSOR_T
{
public:
    BOOL openPort( char* devname, int mportnum, unsigned long buad, unsigned long byte_size );
    BOOL closePort(void);

    BOOL rcvPacket(void);

    char rxbuff[rxbuff_size];

    double sensorData_temp_r[sensorDataNum]; // SUDONG
    double sensorData_temp[sensorDataNum];   // SUDONG

    void requestThreadExit(void);

protected:
    BOOL        portConnected = FALSE;  // Open/Closed indicating flag
    BOOL command_on = FALSE;            // Command On/Off flag

private:
    int Tp;
    pthread_t Thread1;

    struct termios oldtio, newtio;

    bool threadExitRequested = false;

};// class SENSOR_T

/////////////////////////////////////////////////////


void *p_function(void * pSerial)
{
	( (SENSOR_T *)pSerial )->rcvPacket();

	return NULL;
};


void SENSOR_T::requestThreadExit(void)
{
    threadExitRequested = true;
}

BOOL SENSOR_T::openPort( char* devname, int mportnum, unsigned long baud, unsigned long byte_size )
{
    char port[20];
    sprintf(port,"%s%d", devname, mportnum);
    printf("port is opening...");
    Tp = open(port, O_RDWR | O_NOCTTY | O_NDELAY );
    if (Tp == -1 )
    {
        printf("cannot open the serial port");
        return FALSE;
    }
    printf("we opened serial port: %s\n", port);
    
    portConnected = TRUE;
    
    usleep(350);


    // port setting
    //struct termios oldtio, newtio;

	tcgetattr(Tp,&oldtio); /* save current serial port settings */
	bzero(&newtio, sizeof(newtio)); /* clear struct for new port settings */

	// newtio.c_cflag = baud | byte_size | CLOCAL | CREAD; // KSH
    newtio.c_cflag = baud | byte_size;

    // SUDONG
    newtio.c_cflag &= ~PARENB;
    newtio.c_cflag &= ~CSTOPB;
    newtio.c_cflag &= ~CSIZE;
    newtio.c_cflag |= CS8;
    newtio.c_cflag &= ~CRTSCTS;
    newtio.c_cflag |= CREAD | CLOCAL;

    newtio.c_lflag |= ICANON;// &= ~ICANON;
    newtio.c_lflag &= ~ECHO;
    newtio.c_lflag &= ~ECHOE;
    newtio.c_lflag &= ~ECHONL;
    newtio.c_lflag &= ~ISIG;
    newtio.c_iflag &= ~(IXON | IXOFF | IXANY);
    newtio.c_iflag &= ~(IGNBRK|BRKINT|PARMRK|ISTRIP|INLCR|IGNCR|ICRNL);

    newtio.c_oflag &= ~OPOST;
    newtio.c_oflag &= ~ONLCR;

    newtio.c_cc[VTIME] = 5;
    newtio.c_cc[VMIN] = 0;

    cfsetispeed(&newtio, baud);
    cfsetospeed(&newtio, baud);
    // SUDONG

    if (tcflush(Tp, TCIOFLUSH) != 0){
        perror("Error flushing serial port");
        return 1;
    }

	if (tcsetattr(Tp,TCSANOW,&newtio) != 0){
        printf("Error %i from tcsetattr: %s\n", errno, strerror(errno));
        return 0;
    }

    tcsetattr(Tp,TCSAFLUSH,&newtio);

    ioctl(Tp, TCFLSH, 2);

    /* THREAD */
    int result = pthread_create( &Thread1, NULL, p_function, (void *)this );
	if( result != 0 ) {
		printf("\nCan't create read thread");
		closePort();
	}
    else
        printf("THREAD YES\n");

    return TRUE;

}


BOOL SENSOR_T::closePort(void)
{
    tcflush(Tp, TCIFLUSH);         // SUDONG
    tcsetattr(Tp,TCSANOW,&oldtio); // SUDONG

    // Request the thread to exit
    requestThreadExit();

    // Wait for the thread to join
    pthread_join(Thread1, NULL);   

    close(Tp);
    portConnected = FALSE; // flag

    return TRUE;
}

BOOL SENSOR_T::rcvPacket(void)
{

    memset(rxbuff, 0x00, rxbuff_size * sizeof(char));
    // int rxbuff_index = 0;

    while( portConnected && !threadExitRequested )
    {

        //char buf[127] = {0,};
        char buf[127] = {0,};

        // int bytes_read = read(Tp, &buf, sizeof(buf));
        read(Tp, &buf, sizeof(buf));

        /* // KSH
        buf[bytes_read] = '\0';

		if( bytes_read <= 0 )
		{
			//usleep( 1000 ); // just sleep.
			continue;
		}  

        if (bytes_read == -1)
        {
            perror("Error reading from serial port");
            return 1;
        }

        // data copy
		for( int i = 0; i < bytes_read; i++)
		{
			rxbuff[rxbuff_index + i] = buf[i];
		}
		rxbuff_index += bytes_read;

		// find SOP
		int found_idx = -1;
		for (int i = 0; i < rxbuff_index; i++)
		{
			if (rxbuff[i] == '\n') // SOP
			{
				found_idx = i;      // usually 1~16
				break;
			}
		}

        // if the index of SOP is not first(0), shift received data....
		if (found_idx != 0) 
		{
			for (int i = 0; i < (rxbuff_index - found_idx); i++)
			{
				rxbuff[i] = rxbuff[i + found_idx];
			}
			// printf("SHIFT\n");
			rxbuff_index = rxbuff_index - found_idx;
		}
        */ // KSH
        
        // char* tok_ = strtok(rxbuff, ",");
        char* tok_ = strtok(buf, ","); // SUDONG

        int ii = 0;
        while(tok_!=NULL)
        {
            if (ii<sensorDataNum)
            {
                sensorData_temp_r[ii] = atof(tok_);
                // std::cout << sensorData[ii]<< std::endl;
                ii+=1;
            }
            else
                break;
            tok_ = strtok(NULL,",");
        }


        // LPF
        for (int j=0; j<4; j++)
        {
        sensorData_temp[j] = sensorData_temp_r[j];
        g_sensorData[j] = static_cast<float>(sensorData_temp[j]);
        }

        // for (int j = 0; j < 4; j++)
        // {
        //     std::cout << sensorData_temp[j];
        //     if (j < 3)
        //     std::cout << ", ";
        // }
        // std::cout << std::endl;

        // rxbuff_index = 0;

        usleep(1000); // 1ms

    }

    return TRUE;
}


/////////////////////////////////////////////////////////////
/////////////////////////////////////////////////////////////
/////////////////////////////////////////////////////////////

// class variable
SENSOR_T T1;

int main(int argc, char *argv[])
{

    char devName[] = "/dev/ttyACM";
    T1.openPort( devName, portnum, baud, byte_size );
	usleep(1000000);  // 1 second

    rclcpp::init(argc, argv);
    auto node = std::make_shared<SensorT_Publisher>();
    rclcpp::spin(node);
    rclcpp::shutdown();

    T1.closePort();
    usleep(1000000); // 1 second
	
    return 0;
}