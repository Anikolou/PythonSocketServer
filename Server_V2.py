from struct import pack, unpack_from
import socket
import select

def get_max(numbers):
    if not numbers:
        return None
    max_number = numbers[0]
    for number in numbers:
        if number > max_number:
            max_number = number
    return max_number

def mergesort(numbers):
    if len(numbers) <= 1:
        return numbers
    mid = len(numbers) // 2
    left = mergesort(numbers[:mid])
    right = mergesort(numbers[mid:])
    return sort(left, right)

def sort(left, right):
    sorted_arr = []
    i = j = 0
    while i < len(left) and j < len(right): # break the array in half until only 1 element remains and then merge
        
        if left[i] < right[j]:                  # if the left element is smaller than the right element, we add the left element to the sorted array and increment index i, otherwise we add the right element to the sorted array and increment index j
            sorted_arr.append(left[i])
            i += 1
        else:
            sorted_arr.append(right[j])
            j += 1
                                                # remaining elements
    while i < len(left):
        sorted_arr.append(left[i])
        i += 1
    while j < len(right):
        sorted_arr.append(right[j])
        j += 1 
    return sorted_arr

def intersection(A, B):
    both = []
    for x in A:
        if x in B and x not in both:        # we check if the element exists in both lists and if it hasn't already been added to the 'both' array to avoid duplicates in the result 
            both.append(x)
    return both

def handle_client(conn, addr, state):
    try:
        if state['phase'] == 'WAITING_OP_ID':
            msg = conn.recv(2048).decode('utf-8')
            print(f"Message received from {addr}: {msg}") # we print from which client we received the message and what the received message contains

            if not msg:
                print(f"Client {addr} disconnected.") # if we didn't receive any message, it means the client has disconnected and we close the connection with them
                return False           # generally we return False to close the connection with the client after communication is complete, unless we want to keep the connection open for further communication (we return True)
            
            try: 
                op_id = int(msg)        # we try to convert the operation sent by the client to an integer and if we fail, it means the client's choice is invalid
                if op_id in [1, 2, 3]:
                    response  = 0
                    conn.sendall(pack('!H', response)) # we pack the status code as an unsigned short to send it to the client so they know if everything is ok and can send us their data
                    state['phase'] = 'WAITING_HEADER'
                    state['op_id'] = op_id # we save the operation the specific client wants to execute in the client's state saved in the client_states dictionary to use it when we receive the client's data
                                           # on return True, handle_client terminates, which means the op_id would be lost. However, because we keep it in the dictionary, we have the op_id ready.
                                           
                    print(client_states[conn]) # we print the client's state to see what stage of communication they are in and what operation they want to execute
                    
                    return True # Return to the poller to wait for the data, keeping the connection open
                else: 
                    conn.sendall(pack('!H', 1))
                    return False
            except ValueError:
                conn.sendall(pack('!H', 2))
                return False 
                
        elif state['phase'] == 'WAITING_HEADER': # if the client sent us an operation that is not 1, 2 or 3, it means the client's choice is invalid
                header = conn.recv(6) # we receive the bytes containing the lengths of the data that will follow
                if not header:
                    print(f"Client {addr} disconnected.") # if we didn't receive any message, it means the client has disconnected and we close the connection with them
                    return False
                
                len1  = unpack_from('!H', header, 2)[0]
                len2  = unpack_from('!H', header, 4)[0]
                data_length  = len1 + len2
                padding_length = (4 - (6 + data_length) % 4) % 4
                
                state['len1'] = len1 # we save the length of the first list in the client's state saved in the client_states dictionary to use it when we receive the client's data
                state['len2'] = len2 # we save the length of the second list in the client's state saved in the client_states dictionary to use it when we receive the client's data
                state['padding_length'] = padding_length # we save the length of the padding in the client's state saved in the client_states dictionary to use it when we receive the client's data
                state['bytes_to_read'] = data_length + padding_length # we save the total length of the data we will receive (data + padding) in the client's state saved in the client_states dictionary to use it when we receive the client's data
                state['phase'] = 'WAITING_PAYLOAD' # we change the stage
                return True # Return to the poller to wait for the data, keeping the connection open
                
        elif state['phase'] == 'WAITING_PAYLOAD':
                op_id = state['op_id']
                len1 = state['len1']
                len2 = state['len2']
                to_read = state['bytes_to_read']
                
                print(client_states[conn]) # we print the client's state to see what stage of communication they are in and what operation they want to execute
            
                total_received = conn.recv(to_read) 
                data1_str = total_received[:len1].decode('utf-8')
                data2_str = total_received[len1:len1+len2].decode('utf-8')
            
                status_code = 0
                

                # We unpack the data depending on the operation we want to execute
                if op_id == 1:
                    try:
                        # we try to convert the data sent by the client into numbers, and if we fail, it means the data is incorrect.
                        numbers = list(map(int, data1_str.split()))
                        if len(numbers) == 0: status_code = 2 # for data format error status code = 2
                        else:
                            for num in numbers:
                                if num < -100 or num > 100:
                                    status_code = 1 # for numerical errors (out of bounds) status code = 1
                                    break
                    except ValueError: status_code = 2
                
                elif op_id == 2:
                    try:
                        numbers = list(map(float, data1_str.split()))
                        if len(numbers) == 0: status_code = 2
                        else:
                            for num in numbers:
                                if num < 0 or num > 200:
                                    status_code = 1
                                    break
                    except ValueError: status_code = 2
        
                elif op_id == 3:
                    try:
                        A = list(map(int, data1_str.split()))
                        B = list(map(int, data2_str.split()))
                        if len(A) < 2 or len(A) > 10 or len(B) < 2 or len(B) > 10:
                            status_code = 2
                        else:
                            for num in A + B:
                                if num < 0 or num > 60000:
                                    status_code = 1
                                    break
                    except ValueError: status_code = 2
            
                conn.sendall(pack('!H', status_code)) # we pack the status code as an unsigned short to send it to the client so they know if there was a problem with the data they sent or if everything is fine
            
                if status_code != 0:
                    state ['phase'] = 'WAITING_HEADER' # if there was a problem with the data sent by the client, we reset the client's communication stage to 'WAITING_OP_ID' to wait for them to send the operation they want to execute again
                    return True # if there was a problem with the data sent by the client, we don't execute the operation and return True to wait for new data
            
                # Send response to the client depending on the operation
                if op_id == 1:
                    print(f'[{addr}] Numbers received for op 1:', numbers)
                    ans = get_max(numbers)
                    if ans is not None: conn.sendall(pack('!b', ans)) # we pack the response to send it to the client
        
                elif op_id == 2:
                    print(f'[{addr}] Numbers received for op 2:', numbers)
                    ans = mergesort(numbers)
                    # we send the length of the list of numbers and then we pack the numbers as float
                    response = pack('!H', len(ans)) + pack('!' + 'f' * len(ans), *ans)
                    conn.sendall(response)
        
                elif op_id == 3:
                    print(f'[{addr}] Numbers received for op 3 - List A:', A)
                    print(f'[{addr}] Numbers received for op 3 - List B:', B)
                    ans = intersection(A, B)
                    # we send the length of the list of numbers and then we pack the numbers as unsigned short
                    response = pack('!H', len(ans)) + pack('!' + 'H' * len(ans), *ans)
                    conn.sendall(response)
            
                return False # we return False to close the connection with the client after communication is complete

    except BlockingIOError:
        return True # if we encounter a BlockingIOError, it means we haven't received all the data we are expecting from the client yet, so we return True to wait to receive the remaining data
    except Exception as e:
        print(f"Error handling client {addr}: {e}") # if we face any problem during communication with the client, we print the error
        return False

serverIP = ''
serverPort = 12345
close = False

with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as serverSocket:
    serverSocket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    serverSocket.bind((serverIP, serverPort))
    print ("The server is ready to receive at port", str(serverPort))
    serverSocket.listen()
    serverSocket.setblocking(0)
    
    poller = select.poll() # we set up the poller to handle multiple connections simultaneously
    poller.register(serverSocket, select.POLLIN) # we register the serverSocket with the poller to wait for events from it, this way we will know if a client is requesting a connection
    
    client_sockets = [] # we keep the client sockets in a list to iterate through it and find which socket has which event
    client_states = {} # dictionary to store the state of each client (at what stage of communication they are) with the client's socket as the key and another dictionary as the value containing information about the client's state, like the communication stage and the operation they want to execute
    conns = 0 # how many connections we have accepted so far, if we reach 5 we will close the server socket so we don't accept other connections
    
    while not close:
        fdVsEvent = poller.poll(1000) # we wait for events on the sockets for 1 second
        
        for descriptor, Event in fdVsEvent:
            
            if descriptor == serverSocket.fileno(): # if the event concerns the server socket, it means we have a new connection from a client
                conn, addr = serverSocket.accept()
                print("Connected by:", addr)
                
                conn.setblocking(0)
                poller.register(conn, select.POLLIN) # we register the new client socket with the poller to wait for events on it
                client_sockets.append(conn) # we add the new client socket to the list of client sockets
                
                client_states[conn] = {'phase': 'WAITING_OP_ID'} # we initialize the state of the newly connected client in the client_states dictionary, setting their communication stage to 'WAITING_OP_ID' so we know we are waiting for them to send the operation they want to execute
                conns += 1 # we increase the number of connections we have accepted
                
                if conns == 5: # if we have accepted 5 connections, we close the server socket so we don't accept any more connections
                    print("Maximum number of connections reached.")
                    poller.unregister(serverSocket) # we unregister the server socket from the poller so we don't wait for events on it
                    serverSocket.close()
            
            else:
                current = None # we initialize the 'current' variable through which we will access the list of client sockets
                for sock in client_sockets:
                    if sock.fileno() == descriptor: # if the event concerns one of the client sockets, it means we have data to read
                        current = sock
                        break # We find it and save it in the 'current' variable to use it later
                
                if current is not None:
                    # if the handle_client function returns False, it means the communication is complete or there was an error, so we close the connection
                    if handle_client(current, current.getpeername(), client_states[current]) == False:
                        print("Closing connection with client:", current.getpeername())
                        poller.unregister(current) # we unregister the client socket from the poller
                        current.close() # we close the client socket
                        client_sockets.remove(current) # we remove the client socket from the client_sockets list
                        del client_states[current] # we delete the client's state from the client_states dictionary

        # When we have accepted the maximum number of simultaneous clients and all clients have finished communicating and disconnected, it means we can terminate the program
        if conns >= 5 and len(client_sockets) == 0:
            close = True
            print("Everyone is done. Closing...")