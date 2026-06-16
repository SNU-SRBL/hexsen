#pragma once

#include <iostream>
#include <fstream>
#include <string>
#include <cstdio>
#include <termios.h>
#include <stdio.h>
#include <cstring>
#include <stdlib.h>
#include <fcntl.h>
#include <sys/mman.h>
#include <unistd.h>
#include <time.h>
#include <chrono>
#include <thread>
#include <mutex>
#include <ctime>
#include <stdint.h>
#include <sys/ioctl.h>
#include <linux/types.h>
#include <linux/spi/spidev.h>
#include <cmath>
#include <vector>

using namespace std;

namespace sensorcpp {

class serial {
private:
	bool continue_signal = true;
	int fd;
	chrono::duration<double> sec;
	chrono::system_clock::time_point now;
	chrono::system_clock::time_point last_update_imu_[2];
	bool isUpdatedImuUsed[2] = {false, false};
	mutable std::mutex imu_mutex_;  // For thread-safe access to imuData

public:

	float* imuData = new float[18]; // 9*2
	serial(const char *device, const int baud);
	~serial();
	int serialOpen(const char *device, const int baud);
	void serialWrite(const char*s);
	int serialRead(uint8_t *buffer);
	int serialReadLine(unsigned int limit, uint8_t *buffer);
	int readIMU();
	void stopReading();
    void getData(float* data);
};

}  // namespace sensorcpp
