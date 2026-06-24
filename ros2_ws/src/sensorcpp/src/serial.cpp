#include "sensorcpp/serial.hpp" // #include "serial.hpp"

using namespace std;

namespace sensorcpp {

vector<string> split_comma(uint8_t *incomingData, char delimiter) {
    vector<string> answer;
	string temp("");

	int i = 0;

	while(true){
		if (incomingData[i] == delimiter){
			answer.push_back(temp);
			temp = "";
		}
		else if (incomingData[i] == 0){
			answer.push_back(temp);
			break;
		}
		else{
			temp += incomingData[i];
		}
		i++;
	}

    return answer;
}

serial::serial(const char *device, const int baud) {
	this->serialOpen(device, baud);
	for (int i = 0; i < 20 ; i++){
		this->imuData[i] = 0;
	}
}

serial::~serial() {

}

int serial::serialOpen(const char *device, const int baud) {
	struct termios options;
	speed_t myBaud;
	int     status, fd;

	switch (baud)
	{
	case      50:	myBaud = B50; break;
	case      75:	myBaud = B75; break;
	case     110:	myBaud = B110; break;
	case     134:	myBaud = B134; break;
	case     150:	myBaud = B150; break;
	case     200:	myBaud = B200; break;
	case     300:	myBaud = B300; break;
	case     600:	myBaud = B600; break;
	case    1200:	myBaud = B1200; break;
	case    1800:	myBaud = B1800; break;
	case    2400:	myBaud = B2400; break;
	case    4800:	myBaud = B4800; break;
	case    9600:	myBaud = B9600; break;
	case   19200:	myBaud = B19200; break;
	case   38400:	myBaud = B38400; break;
	case   57600:	myBaud = B57600; break;
	case  115200:	myBaud = B115200; break;
	case  230400:	myBaud = B230400; break;
	case  460800:	myBaud = B460800; break;
	case  500000:	myBaud = B500000; break;
	case  576000:	myBaud = B576000; break;
	case  921600:	myBaud = B921600; break;
	case 1000000:	myBaud = B1000000; break;
	case 1152000:	myBaud = B1152000; break;
	case 1500000:	myBaud = B1500000; break;
	case 2000000:	myBaud = B2000000; break;
	case 2500000:	myBaud = B2500000; break;
	case 3000000:	myBaud = B3000000; break;
	case 3500000:	myBaud = B3500000; break;
	case 4000000:	myBaud = B4000000; break;

	default:
		return -2;
	}

	if ((fd = open(device, O_RDWR | O_NOCTTY | O_NDELAY | O_NONBLOCK)) == -1)
		return -1;

	fcntl(fd, F_SETFL, O_RDWR);

	// Get and modify current options:

	tcgetattr(fd, &options);

	cfmakeraw(&options);
	cfsetispeed(&options, myBaud);
	cfsetospeed(&options, myBaud);

	options.c_cflag |= (CLOCAL | CREAD);
	options.c_cflag &= ~PARENB;
	options.c_cflag &= ~CSTOPB;
	options.c_cflag &= ~CSIZE;
	options.c_cflag |= CS8;
	options.c_lflag &= ~(ICANON | ECHO | ECHOE | ISIG);
	options.c_oflag &= ~OPOST;

	options.c_cc[VMIN] = 0;
	options.c_cc[VTIME] = 100;	// Ten seconds (100 deciseconds)

	tcsetattr(fd, TCSANOW, &options);

	ioctl(fd, TIOCMGET, &status);

	status |= TIOCM_DTR;
	status |= TIOCM_RTS;

	ioctl(fd, TIOCMSET, &status);

	usleep(10000);	// 10mS

	this->fd = fd;
	
	return 1;

}

void serial::serialWrite(const char *s) {
	write(this->fd, s, strlen(s));
	return;
}

int serial::serialRead(uint8_t *buffer) {
	if (read(this->fd, buffer, 1) != 1) return -1;
	
	return 1;

}

int serial::serialReadLine(unsigned int limit, uint8_t *buffer) {

	uint8_t ch = 0;
	int bytesRead = 0;
	for (int i = 0; i < limit; i++)
	{
		bytesRead += serialRead(&ch);
		buffer[i] = ch;

		if ((char)ch == '\n') break;

	}

	return bytesRead;
}

int serial::readIMU() {
	uint8_t incomingData[255];
	uint8_t trimData[255];
	int nread;
	int num = 0;
	string num_temp = "";
	while (this->continue_signal) {
		nread = this->serialReadLine(255, incomingData);
		if (nread > 0) {
			num_temp = "";
			incomingData[nread - 2] = 0;
			try{
				vector<string> result = split_comma(incomingData, ',');
				num_temp += result.at(0).at(4);
				num = stoi(num_temp);
				{
					std::lock_guard<std::mutex> lock(imu_mutex_);
					for (int i = 0; i <10; i++){
						this->imuData[10 * num + i] = stof(result.at(i+1));
					}
				}
				this->last_update_imu_[num] = chrono::system_clock::now();
                this->isUpdatedImuUsed[num] = false;
			}
			catch(...){}
		}
	}
	cout << "IMU Serial Reading End" << endl;
	return 1;
}

void serial::stopReading(){
    this->continue_signal = false;
}

void serial::getData(float* data){
    {
        std::lock_guard<std::mutex> lock(imu_mutex_);
        for (int i = 0; i < 20; i++){
            data[i] = this->imuData[i];
        }
    }
    this->isUpdatedImuUsed[0] = true;
    this->isUpdatedImuUsed[1] = true;
}

}  // namespace sensorcpp