import time
import socket
import sys
import threading
import math
import os
import os.path
import traceback

# Timeout Interval for the packet to get acknowledged
TIMEOUT_VALUE = 1

# Field Value for the Data Packet and the Acknowledged Packet
DATA_PACKET_FIELD = int('0101010101010101',2)
ACK_PACKET_FIELD = int('1010101010101010',2)

# List to hold the data packets
packets = []

# Dictionary to keep track of the packets time value
packets_time = {}

# Total number of packets to be send (Initaily initializing with 1)
number_of_packets = 1

# Total Number of packets acknowledged till now
packets_acknowledged = 0

# Expected ACK value
ack_expected = 0

lock = threading.Lock()

def N_PACKETS_TRANSMITTED(seq_no_to_send,ack_expected,N):
	"""
	To check weather N packets in the window are sent to the Server
	Arguments:
		seq_no_to_send 	: Current Sequence Number To Send
		ack_expected	: Expected Value of the Acknowledgement
		N 				: Window Size
	"""
	# Returns true if the N packets are transmitted i.e. 
	# difference between the sequence number of expected ack and sequence number of next packet to send 
	# is becoming equal to greater to window size
	return seq_no_to_send - ack_expected >= N

def N_GREATER_THAN_TOTAL_PACKETS(seq_no_to_send,ack_expected,N,number_of_packets):
	"""
	To check weather window size(N) is greater than total number of packets
	Arguments:
		seq_no_to_send 		: Current Sequence Number To Send
		ack_expected		: Expected Value of the Acknowledgement
		N 					: Window Size
		number_of_packets 	: Total Number of Packets
	"""
	# Returns True if the total number of packts are less than the window size 
	# and if the sequence number expected is less than the sequence number to send else false
	return number_of_packets <= N and ack_expected < seq_no_to_send

def TIMEOUT(packets_time,ack_expected):
	"""
	To check if the packet has timed out
	Arguments:
		packets_time 		: Packets initial time value
		ack_expected		: Expected Value of the Acknowledgement
	"""
	# Returns true if the packet has timed out else False
	return time.time() - packets_time[ack_expected] >= TIMEOUT_VALUE 

def RETRANSMIT(seq_no_to_send,ack_expected,packets,client_socket,server_host_name,server_port):
	"""
	To retransmit the packets in the current window
	Arguments:
		seq_no_to_send 		: Current Sequence Number To Send
		ack_expected		: Expected Value of the Acknowledgement
		packets 			: List ontaining all the packets
		client_socket		: Client Socket
		server_host_name	: Host Name of the Server
		server_port			: Post # of the Server
	"""
	print('Timeout, Sequence Number = ' + str(ack_expected)) #Printing the packet that is timed out

	# Running the loop from the packet with sequence number lost to the last sequence number send
	for sequence_number in range(ack_expected,seq_no_to_send):
		packets_time[sequence_number] = time.time() #Reseting the timer of retransmitted packet
		client_socket.sendto(packets[sequence_number].encode('UTF-8','ignore'), (server_host_name,server_port)) #Retransmitting the packet

def TIMEOUT_RETRANSMIT(seq_no_to_send,ack_expected,packets,client_socket,server_host_name,server_port,packets_time):
	"""
	To retransmit the packets in the current window if the packet is timed out
	Arguments:
		seq_no_to_send 		: Current Sequence Number To Send
		ack_expected		: Expected Value of the Acknowledgement
		packets 			: List ontaining all the packets
		client_socket		: Client Socket
		server_host_name	: Host Name of the Server
		server_port			: Post # of the Server
		packets_time    	: Packets initial time value
	"""
	try:
		# If the packet timeout, then retransmit
		if TIMEOUT(packets_time,ack_expected):
			RETRANSMIT(seq_no_to_send,ack_expected,packets,client_socket,server_host_name,server_port)
	except KeyError:
		pass

def get_checksum(data):
	"""
	Calculate the Checksum of the data
	Arguments:
		data : Data Value in String for which the checksum is to be calculated
	"""
	sm = 0
	size = len(data) - len(data) % 2 # Storing the length if data, if data is odd, then data length else data length -1
	
	# Running loop fo each 2 byte data in the data
	for i in range(0, size, 2): 
		shift = ord(data[i]) + (ord(data[i+1]) << 8) #Adding data and its 8bit left shifted part
		chk = sm + shift #Concating the shift to the total data
		sm = (chk & 0xffff) + (chk >> 16) #Carry Around add
	return ~sm & 0xffff #Returning the checksum

def check_arguments(file_name,N,MSS):
	"""
	Check if the provided arguments are within the specified range or not
	Arguments:
		file_name 	: Input File Path
		N 			: Window Size
		MSS 		: Maximum Segment Size
	"""
	# Checking if the given input file exists on the system or not
	if(not os.path.exists(file_name)):
		print("FileError: The defined file doesn't exist, Please check the name of the file")
		quit()

	# Checking for valid window size (N)
	if(N<=0):
		print("Window Size Error: Invalid Window size")
		quit()

	# Checking for Maximum Segement Size (MSS)
	if(MSS<=0):
		print("MSS Error: Invalid maximum segment size (MSS)")
		quit()

def send_packet(client_socket,server_host_name,server_port,N):
	"""
	Send the Packet to the specified Server
	Arguments:
		client_socket		: Client Socket
		server_host_name	: Host Name of the Server
		server_port			: Post # of the Server
		N 					: Window Size
	"""

	global lock
	global packets_time
	global packets_acknowledged
	global ack_expected
	global number_of_packets
	global packets

	# Initialising the Sequence number with 0
	seq_no_to_send = 0

	# While there are packets left to be acknowledged i.e. not all packets are recieved by the server
	while packets_acknowledged <  number_of_packets:

		# Case when all packets in the window are transmitted
		while N_PACKETS_TRANSMITTED(seq_no_to_send,ack_expected,N):
			lock.acquire()
			if ack_expected < seq_no_to_send and ack_expected in packets_time:
				TIMEOUT_RETRANSMIT(seq_no_to_send,ack_expected,packets,client_socket,server_host_name,server_port,packets_time)
			lock.release()

		# Case when window size(N) is greater than total number of packets
		lock.acquire()
		if N_GREATER_THAN_TOTAL_PACKETS(seq_no_to_send,ack_expected,N,number_of_packets) and ack_expected in packets_time:
			TIMEOUT_RETRANSMIT(seq_no_to_send,ack_expected,packets,client_socket,server_host_name,server_port,packets_time)
		lock.release()

		# Case when any packet is not yet recieved by the Server
		lock.acquire()
		if ack_expected < seq_no_to_send and ack_expected in packets_time:
			TIMEOUT_RETRANSMIT(seq_no_to_send,ack_expected,packets,client_socket,server_host_name,server_port,packets_time)
		lock.release()

		# Sending the Packet to the Server
		lock.acquire()
		if seq_no_to_send < number_of_packets:
			packets_time[seq_no_to_send] = time.time()
			client_socket.sendto(packets[seq_no_to_send].encode('UTF-8','ignore'), (server_host_name,server_port))
			seq_no_to_send += 1
		lock.release()


def get_acknowledgement(client_socket):
	"""
	Recieve Acknowledgement from specified Server
	Arguments:
		client_socket		: Client Socket
	"""

	global lock
	global packets_time
	global packets_acknowledged
	global ack_expected
	global number_of_packets

	try:
		# While there are packets left to be acknowledged
		while packets_acknowledged <  number_of_packets:
			acknowledgement, serverAddress = client_socket.recvfrom(2048) #Recieviing data from the Server
			acknowledgement = acknowledgement.decode('UTF-8','ignore') #Decoding the acknowledgement
			ack_seq_nr = int(acknowledgement[0:8],16) #acknowledgement sequence number
			ack_packet_field = int(acknowledgement[12:],16) #Acknowledged Packet Field Value

			# If the acknowledgement recieved was for the expected packet
			if ack_packet_field == ACK_PACKET_FIELD:
				lock.acquire()
				packets_acknowledged += 1 #Incrementing the Total Number of packets acknowledged
				ack_expected += 1 #Incrementing the Expected ACK value
				del packets_time[ack_seq_nr] #Deleting the acknowledged packet from the time list
				lock.release()
	except:
		traceback.print_exc()
		print("ERROR: While recieving Acknowledgement, Socket Closed")
		client_socket.close()


def rdt_send(server_host_name,server_port,file_name,N,MSS):
	"""
	Function to read data from a specified file and transfer the data to the Simple-FTP Server
	Arguments:
		server_host_name	: Host Name of the Server
		server_port			: Post # of the Server
		file_name 			: Input File Path
		N 					: Window Size
		MSS 				: Maximum Segment Size
	"""

	# Storing the Startig Time of the Process
	begin_time = time.time()

	# Checking for invalid input values
	check_arguments(file_name,N,MSS)

	# Printing the Arguments for the transfer process
	print()

	print("Host Name: " + str(server_host_name))
	print("Port #: " + str(server_port))
	print("File Name: " + file_name)
	print("Window Size (N): " + str(N))
	print("Maximum Segment Size (MSS): " + str(MSS))

	print()

	global packets
	global number_of_packets

	# Creating UDP Socket
	client_port = 7735
	client_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

	# Opening the file and getting the total count of packets
	data_file = open(file_name,'rb')
	file_size = os.path.getsize(file_name)
	number_of_partitions = math.ceil(file_size/MSS)

	# Reading the first MSS data and initializing the sequence number with 0
	data_of_MSS_size = data_file.read(MSS)
	sequence_number = 0

	# Looping while there is no more MSS size of data left
	while(data_of_MSS_size):

		data = str(data_of_MSS_size,'UTF-8',errors='replace') #Encoding the data from bytes to string
		data_to_send = data
		checksum = get_checksum(data) #Computing the Checksum
		checksum = '{:04x}'.format(checksum) #Convertring the Checksum to 16-bit or 4 byte HEXADECIMAL VALUE
		seq_nr = '{:08x}'.format(sequence_number) #Convertring the Sequence Number to 32-bit or 8 byte HEXADECIMAL VALUE
		data_packet_field = '{:04x}'.format(DATA_PACKET_FIELD) #Convertring the Data Field Value to to 16-bit or 4 byte HEXADECIMAL VALUE
		packet = seq_nr + checksum + data_packet_field + data_to_send #Creating the complete packet by adding the header and the Data
		packets.append(str(packet)) #Storing the packet in packets list
		data_of_MSS_size = data_file.read(MSS) #Reading next MSS length of data
		sequence_number += 1 #Incrementing the Sequence Number

	# Sending the last packet as END_OF_FILE to identify all the data has been sent
	end_of_file = "END_OF_FILE"
	data_to_send = end_of_file
	checksum = get_checksum(end_of_file) #Computing the Checksum
	checksum = '{:04x}'.format(checksum) #Convertring the Checksum to 16-bit or 4 byte HEXADECIMAL VALUE
	seq_nr = '{:08x}'.format(sequence_number) #Convertring the Sequence Number to 32-bit or 8 byte HEXADECIMAL VALUE
	data_packet_field = '{:04x}'.format(DATA_PACKET_FIELD) #Convertring the Data Field Value to to 16-bit or 4 byte HEXADECIMAL VALUE
	packet = seq_nr + checksum + data_packet_field + data_to_send #Creating the complete packet by adding the header and the Data
	packets.append(str(packet)) #Storing the packet in packets list

	# Calculating teh total number of packets to be sent
	number_of_packets = len(packets)

	# Creating a Thread for Sending Data and Recieving acknowledgement
	SEND_thread = threading.Thread(target=send_packet,args = (client_socket,server_host_name,server_port,N),name="Thread: Packet Sending")
	ACK_thread = threading.Thread(target=get_acknowledgement,args = (client_socket,),name="Thread: Packet Acknowledgement")

	# Starting the Threads
	SEND_thread.start()
	ACK_thread.start()
	
	# Joining Threads with the main Thread
	ACK_thread.join()
	SEND_thread.join()
	
	# Calculating the Finish Time of the process
	finish_time = time.time()

	# Closing the Socket
	client_socket.close()

	# Returning the Delay(Time tacken by the process)
	return finish_time - begin_time


if __name__ == '__main__':

	# Waiting for the server to start
	time.sleep(0.5)

	# Reading Arguments
	server_host_name = sys.argv[1]
	server_port = int(sys.argv[2])
	file_name = sys.argv[3]
	N = int(sys.argv[4])
	MSS = int(sys.argv[5])
	
	os.system("clear")

	# Calling the funtion to start the transfer
	delay = rdt_send(server_host_name, server_port, file_name, N, MSS)

	# Giving the Delay(Time tacken by the process)
	print()
	print("Total Time Taken(Delay) : " + str(delay) + "ms")

	# Uncomment to Save results in result.txt
	# result = "For N = {}, MSS = {}, the delay is = {} \n".format(str(N),str(MSS),str(delay)) 
	# open('result.txt', 'ab').write(str.encode(result))
