import socket
import sys
import os
import random

# Field Value for the Data Packet and the Acknowledged Packet
DATA_PACKET_FIELD = int('0101010101010101',2)
ACK_PACKET_FIELD = int('1010101010101010',2)

# Dictionary to store all the acknowledged data packets and its data
packets_acknowledged = {}

# Sequence number of the last packet
last_seq_no = float('inf')

# field that is all zeroes
ZERO = 0

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

def discard_packet(p):
	"""
	probabilistic loss service to discard packet
	p 	: probability of packet failure
	"""
	r = round(random.random(),2) #Getting a random value r
	# If random value is 0, re calculate the random value
	while r == 0.0:
		r = round(random.random(),2)

	# Returns True if the random value is less or equal to p
	return r<=p

def check_checksum(data,checksum):
	"""
	Check if the checksum of the received data is correct
	data 		: data received
	checksum 	: Checksum received
	"""
	check = get_checksum(data) #Calculate the checksum of the data received
	# Returns true if the checksum matches
	return check == checksum

def check_arguments(file_name,p):
	"""
	Check if the provided arguments are within the specified range or not
	Arguments:
		file_name 	: Output File Path
		p 			: Probability
	"""
	# Checking if the given outpu file exists on the system or not
	if(not os.path.exists(file_name)):
		print("FileError: The defined file doesn't exist, Please check the name of the file")
		quit()
		
	# Checking for valid probabilistic loss service (p)
	if(p<=0 or p>=1):
		print("Probability Error: Invalid probability value")
		quit()

def write_to_file(packets_acknowledged,file_name,last_seq_no):
	"""
	Write the received packets in the given file
	Arguments:
		packets_acknowledged	: Dictionary containing data for each sequence number
		file_name 				: Output File Path
		last_seq_no 			: Last Sequence Number till which the data exists
	"""
	for packet in range(0,last_seq_no):
		open(file_name, 'ab').write(str.encode(packets_acknowledged[packet]))

def rdt_receive(server_port,file_name,p):
	"""
	Function to receive data from a client and send acknowledgement via Simple-FTP Server
	Arguments:
		server_port	: Post # of the Server
		file_name 	: Output File Path
		p			: Proibability
	"""

	# Checking for invalid input values
	check_arguments(file_name,p)

	# Printing the Arguments for the transfer process
	print()

	print("Server's Port #: " + str(server_port))
	print("File Name: " + file_name)
	print("Probability: " + str(p))

	# Creating UDP Socket
	client_port = 7735
	server_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
	server_host_name = socket.gethostname()
	print("Server's Host Name: " + str(server_host_name))
	print()
	server_socket.bind(('', server_port))

	# Initializing the sequence number with 0
	server_sequence_number = 0

	global packets_acknowledged
	global last_seq_no

	# Receiving data
	while 1:

		# Complete data is received from the client, write data to the specified file
		if(len(packets_acknowledged) == last_seq_no):
			write_to_file(packets_acknowledged,file_name,last_seq_no) #Write data to the specified file
			server_socket.close() # Close the Server Socket
			
			print()
			print("Server Closed")
			print("Data Recieved")
			print("Please check {}".format(file_name))
			break;

		packet, clientAddress = server_socket.recvfrom(2048) #Receiving data from the server
		packet = packet.decode('UTF-8','ignore') #Decoding the data received
		client_sequence_number = int(packet[0:8],16) #Data packet sequence number as received frm client
		checksum = int(packet[8:12],16) #Checksum as received from the client
		data_packet_field = int(packet[12:16],16) # Data Packet Field Value
		data = packet[16:]	# Data from the Client

		# Incrementing the Sequence Number for all the data packets which were received when server_sequence_number < client_sequence_number
		while(server_sequence_number < client_sequence_number and server_sequence_number in packets_acknowledged):
			server_sequence_number += 1 #Incrementing the Sequence Number

		# If the sequence number and the DATA PACKET FIELD matches
		if server_sequence_number == client_sequence_number and data_packet_field == DATA_PACKET_FIELD:
			
			# If the Packet is already received discard and continue
			if(server_sequence_number in packets_acknowledged):
				pass

			# If the Packet is discared by the probabilistic loss service
			elif(discard_packet(p)):
				print('Packet loss, sequence number = '+ str(client_sequence_number))

			# Else if the Checksum matches
			elif(check_checksum(data,checksum)):
				seq_nr = '{:08x}'.format(client_sequence_number) #Convertring the Sequence Number to 32-bit or 8 byte HEXADECIMAL VALUE
				all_zeroes = '{:04x}'.format(ZERO) #Convertring the Zero to 16-bit or 4 byte HEXADECIMAL VALUE
				ack_packet_field = '{:04x}'.format(ACK_PACKET_FIELD) #Convertring the Acknowledgement Field Value to 16-bit or 4 byte HEXADECIMAL VALUE
				acknowledgement = seq_nr + all_zeroes + ack_packet_field # #Creating the complete acknowledgement by adding the header and the Data
				server_socket.sendto(acknowledgement.encode('UTF-8','ignore'), clientAddress) #Send acknowledgement to the Client
				# print(acknowledgement)

				# if the data received is the END OF FILE i.e the last data packet
				if data == "END_OF_FILE":
					last_seq_no = client_sequence_number

				# Else write the recieved data in the output file
				else:
					packets_acknowledged[client_sequence_number] = data

				server_sequence_number += 1 #Incrementing the Sequence Number

		# If the DATA PACKET FIELD matches but the sequence number is of packet with sequence number greater than the expected sequence number
		# i.e. for the case when the expected sequence number packet is dropped but the next packet is received
		elif server_sequence_number < client_sequence_number and data_packet_field == DATA_PACKET_FIELD:
			
			# If the Packet is already received discard and continue
			if(server_sequence_number in packets_acknowledged):
				pass

			# If the Packet is discared by the probabilistic loss service
			elif(discard_packet(p)):
				print('Packet loss, sequence number = '+ str(client_sequence_number))

			# Else if the Checksum matches
			elif(check_checksum(data,checksum)):
				seq_nr = '{:08x}'.format(client_sequence_number) #Convertring the Sequence Number to 32-bit or 8 byte HEXADECIMAL VALUE
				all_zeroes = '{:04x}'.format(ZERO) #Convertring the Zero to 16-bit or 4 byte HEXADECIMAL VALUE
				ack_packet_field = '{:04x}'.format(ACK_PACKET_FIELD) #Convertring the Acknowledgement Field Value to 16-bit or 4 byte HEXADECIMAL VALUE
				acknowledgement = seq_nr + all_zeroes + ack_packet_field # #Creating the complete acknowledgement by adding the header and the Data
				server_socket.sendto(acknowledgement.encode('UTF-8','ignore'), clientAddress) #Send acknowledgement to the Client
				# print(acknowledgement)

				# if the data received is the END OF FILE i.e the last data packet
				if data == "END_OF_FILE":
					last_seq_no = client_sequence_number

				# Else write the recieved data in the output file
				else:
					packets_acknowledged[client_sequence_number] = data

if __name__ == '__main__':

	#Reading Arguments
	server_port = int(sys.argv[1])
	file_name = sys.argv[2]
	p = float(sys.argv[3])

	os.system("clear")

	# Calling the funtion to start the transfer
	rdt_receive(server_port,file_name,p)

	# close_server = input("Close Server? y/n : ")
	# if close_server.lower() == "y":
	# 	exit()