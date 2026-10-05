from struct import *
import socket
import binascii
import sys   #περιέχει την εντολή sys.exit() που μας επιτρέπει να τερματίσουμε το πρόγραμμα σε περίπτωση που ο server δεν είναι διαθέσιμος

serverName = '127.0.0.1'
serverPort = 12345

clientSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

try:
    clientSocket.connect((serverName, serverPort))
    print("Σύνδεση με τον server επιτυχής.")
except ConnectionRefusedError:
    print("O server δεν ειναι διαθέσιμος. Παρακαλώ ξαναπροσπαθήστε αργότερα.")
    sys.exit() #όταν ο client που είναι εκτός ορίων προσπαθήσει να συνδεθεί το OS θα πετάξει error που το πιάνουμε στην try-except και τερματίζουμε το πρόγραμμα 
    
while True:
    
    op_str = input("Επιλέξτε την πράξη που θέλετε να εκτελέσετε (1: Μέγιστο, 2: Ταξινόμηση, 3: Τομή): ")
    clientSocket.sendall(op_str.encode('utf-8'))
    
    reply = clientSocket.recv(2)
    reply = unpack_from('!H' , reply, 0)[0] #λαμβάνουμε την απάντηση του server για το αν η επιλογή μας είναι έγκυρη ή όχι (2 bytes) και την ξεπακετάρουμε ως unsigned short για να δούμε αν μπορούμε να στείλουμε τα δεδομένα μας στον server ή αν πρέπει να επιλέξουμε ξανά πράξη γιατί η επιλογή μας δεν ήταν έγκυρη
    if reply == 0:
        print("Status: OK, μπορείτε να στείλετε τα δεδομένα σας στον server.")
        break
    else:
        print("Μη έγκυρη επιλογή, δοκιμάστε ξανά.")

op_id = int(op_str)

while True:
    input_str1 = ""
    input_str2 = ""
    
    message = pack('!H', op_id) #πακετάρουμε την πράξη που θέλουμε να εκτελέσουμε ως unsigned short (2 bytes)
    
    #Πακετάρουμε τα δεδομένα ανάλογα την περίπτωση
    if op_id == 1:
        print("Εισάγετε μια λίστα ΠΡΟΣΗΜΑΣΜΈΝΩΝ ΑΚΕΡΑΊΩΝ αριθμών ΑΠΌ -100 ΕΩΣ 100 (χωρισμένους με κενό):")
        input_str1 = input()
    
    elif op_id == 2:
        print("Εισάγετε μια λίστα αριθμών ΑΠΌ 0 ΕΩΣ 200 (χωρισμένους με κενό):")
        input_str1 = input()

    elif op_id == 3:
        print("Εισάγετε την πρώτη λίστα αριθμών ΑΠΌ 0 ΕΩΣ 60000 (χωρισμένους με κενό):")
        input_str1 = input()
        print("Εισάγετε την δεύτερη λίστα αριθμών ΑΠΌ 0 ΕΩΣ 60000 (χωρισμένους με κενό):")
        input_str2 = input()

    data1_b = input_str1.encode('utf-8')
    data2_b = input_str2.encode('utf-8')
    
    message = message + pack('!H', len(data1_b)) #πακετάρουμε το μήκος της πρώτης λίστας
    message = message + pack('!H', len(data2_b)) #πακετάρουμε το μήκος της δεύτερης λίστας 
    message = message + data1_b + data2_b #πακετάρουμε τα δεδομενα των 2 λιστων ως bytes

    current_length = len(message)
    padding_length = (4 - current_length % 4) % 4 #υπολογίζουμε το μήκος του padding για να ευθυγραμμίσουμε στα 4 bytes

    if(padding_length>0):
        message = message + pack(str(padding_length)+'x')
            
    print(f'Message in hex to send to server: {binascii.hexlify(message)}')

    clientSocket.sendall(message) #στέλνουμε το πακεταρισμένο μήνυμα στον server
    
    status_b= clientSocket.recv(2)   #λαμβάνουμε το status code που μας στέλνει ο server ως απάντηση (2 bytes) και το ξεπακετάρουμε ως unsigned short για να δούμε αν η επεξεργασία των δεδομένων μας από τον server ήταν επιτυχής ή αν αντιμετώπισε κάποιο πρόβλημα με τα δεδομένα που του στείλαμε
    status = unpack_from('!H', status_b, 0)[0]
    
    if status == 1:
        print("Status: 1 Ο server αντιμετώπισε πρόβλημα με τα δεδομένα που του στείλαμε. Παρακαλώ ελέγξτε τα δεδομένα σας και δοκιμάστε ξανά.")
        continue
    
    elif status == 0:
        print("Status: 0 Ο server επεξεργάστηκε τα δεδομένα σας με επιτυχία.")
        
    elif status == 2:
        print("Status: 2 Ο server δεν κατάφερε να μετατρέψει τα δεδομένα σας σε ακέραιους. Παρακαλώ ελέγξτε τα δεδομένα σας και δοκιμάστε ξανά.")
        continue
    
    response  = clientSocket.recv(2048) #λαμβάνουμε την απάντηση από τον server (το μέγεθος των δεδομένων που θα λάβουμε εξαρτάται από την πράξη που εκτελέσαμε και το μέγεθος των λιστών που στείλαμε)

    if op_id == 1:
        result = unpack_from('!b', response, 0)[0] #ξεπακετάρουμε το αποτέλεσμα ως signed char
        
    elif op_id == 2:
        length = unpack_from('!H', response, 0)[0] #ξεπακετάρουμε το μήκος της λίστας αποτελεσμάτων
        result = unpack_from('!' + 'f' * length, response, 2) #ξεπακετάρουμε τα αποτελέσματα ως float ξεκινάμε μετά τα 2 bytes που περιέχουν το μήκος

    elif op_id == 3:
        length = unpack_from('!H', response, 0)[0] #ξεπακετάρουμε το μήκος της λίστας αποτελεσμάτων
        result = unpack_from('!' + 'H' * length, response, 2) #ξεπακετάρουμε τα αποτελέσματα ως unsigned short ξεκινάμε μετά τα 2 bytes που περιέχουν το μήκος

    print("Response from server:", str(result))
    clientSocket.close()
    break