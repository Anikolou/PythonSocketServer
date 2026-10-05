from struct import *
import socket
import binascii
import sys   # contains the sys.exit() command which allows us to terminate the program in case the server is unavailable

serverName = '127.0.0.1'
serverPort = 12345

clientSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

try:
    clientSocket.connect((serverName, serverPort))
    print("Connection to the server successful.")
except ConnectionRefusedError:
    print("The server is unavailable. Please try again later.")
    sys.exit() # when an out-of-bounds client tries to connect, the OS will throw an error that we catch in the try-except block and terminate the program 
    
while True:
    
    op_str = input("Select the operation you want to execute (1: Maximum, 2: Sort, 3: Intersection): ")
    clientSocket.sendall(op_str.encode('utf-8'))
    
    reply = clientSocket.recv(2)
    reply = unpack_from('!H' , reply, 0)[0] # we receive the server's response about whether our choice is valid or not (2 bytes) and unpack it as an unsigned short to see if we can send our data to the server or if we must choose an operation again because our choice was invalid
    if reply == 0:
        print("Status: OK, you can send your data to the server.")
        break
    else:
        print("Invalid selection, please try again.")

op_id = int(op_str)

while True:
    input_str1 = ""
    input_str2 = ""
    
    message = pack('!H', op_id) # we pack the operation we want to execute as an unsigned short (2 bytes)
    
    # We pack the data depending on the case
    if op_id == 1:
        print("Enter a list of SIGNED INTEGER numbers FROM -100 TO 100 (separated by space):")
        input_str1 = input()
    
    elif op_id == 2:
        print("Enter a list of numbers FROM 0 TO 200 (separated by space):")
        input_str1 = input()

    elif op_id == 3:
        print("Enter the first list of numbers FROM 0 TO 60000 (separated by space):")
        input_str1 = input()
        print("Enter the second list of numbers FROM 0 TO 60000 (separated by space):")
        input_str2 = input()

    data1_b = input_str1.encode('utf-8')
    data2_b = input_str2.encode('utf-8')
    
    message = message + pack('!H', len(data1_b)) # we pack the length of the first list
    message = message + pack('!H', len(data2_b)) # we pack the length of the second list 
    message = message + data1_b + data2_b # we pack the data of the 2 lists as bytes

    current_length = len(message)
    padding_length = (4 - current_length % 4) % 4 # we calculate the padding length to align to 4 bytes

    if(padding_length>0):
        message = message + pack(str(padding_length)+'x')
            
    print(f'Message in hex to send to server: {binascii.hexlify(message)}')

    clientSocket.sendall(message) # we send the packed message to the server
    
    status_b= clientSocket.recv(2)   # we receive the status code sent by the server as a response (2 bytes) and unpack it as an unsigned short to see if the processing of our data by the server was successful or if it encountered a problem with the data we sent
    status = unpack_from('!H', status_b, 0)[0]
    
    if status == 1:
        print("Status: 1 The server encountered a problem with the data we sent. Please check your data bounds and try again.")
        continue
    
    elif status == 0:
        print("Status: 0 The server processed your data successfully.")
        
    elif status == 2:
        print("Status: 2 The server failed to parse your data. Please check your formatting and try again.")
        continue
    
    response  = clientSocket.recv(2048) # we receive the response from the server (the size of the data we receive depends on the operation we executed and the size of the lists we sent)

    if op_id == 1:
        result = unpack_from('!b', response, 0)[0] # we unpack the result as a signed char
        
    elif op_id == 2:
        length = unpack_from('!H', response, 0)[0] # we unpack the length of the results list
        result = unpack_from('!' + 'f' * length, response, 2) # we unpack the results as float starting after the 2 bytes that contain the length

    elif op_id == 3:
        length = unpack_from('!H', response, 0)[0] # we unpack the length of the results list
        result = unpack_from('!' + 'H' * length, response, 2) # we unpack the results as unsigned short starting after the 2 bytes that contain the length

    print("Response from server:", str(result))
    clientSocket.close()
    break