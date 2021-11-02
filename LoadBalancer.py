from ctypes import sizeof
import socketserver
import socket
import selectors
import types
import logging
import sys
import SCB

#NO.0 ATTENTION, JUMP TO SEGMENT THAT SAYS "THIS IS WHERE THE PROGRAM STARTS" TO UNDERSTAND BETTER
#I USE NO.0, NO.1, NO.2... TO DENOTE READING ORDER OF THE CODE. JUMP TO SEGMENT NO.1 FROM HERE
#THESE NEXT FEW LINES ARE FUNCTIONS DEFINITIONS

#NO.4 finds which server has the minimum data used so far
def findMinData():
    global servers 
    returnPointer = 0
    min = servers[0].totalData
    minPointer = 0

    for val in servers:
        if val.totalData < min:
            returnPointer = minPointer
            min = val.totalData
        minPointer +=1

    return returnPointer


#NO.2 ESTABLISHES CONNECTION
def accept_wrapper(sock):
    conn, addr = sock.accept()  # Should be ready to read
    clientAddress = addr[0]
    clientPort = addr[1]

    message = 'Accepted connection from ' + addr[0] + ":" + str(addr[1])
    logging.info(message)
    print(message)

    #this is just some setup stuff. It's similar to what was seen with the listening socket in NO.1
    conn.setblocking(False)
    data = types.SimpleNamespace(addr=addr, inb=b'', outb=b'')
    events = selectors.EVENT_READ | selectors.EVENT_WRITE
    sel.register(conn, events, data=data)

#NO.3 SERVICES CONNECTION USING ROUND ROBIN POLICY (basically in order)
def service_connection_RR(key, mask):
    #the global keyword refers to a variable declared outside this function. servers and serverPointer were declared in our 'main'
    global servers
    global serverPointer

    sock = key.fileobj
    data = key.data
    #mask is either read or write (i think true for read, false for write)
    if mask & selectors.EVENT_READ:
        recv_data = sock.recv(1024)  # Should be ready to read
        
        if recv_data:
            message = "Recieved Message of size " + str(sys.getsizeof(recv_data)) + "bytes from Client " + data.addr[0] + ":" + str(data.addr[1]) + ":\n" + str(recv_data)
            logging.info(message)
            print(message)
            
            #making a new socket to connect to one of our servers
            socketToServer = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            socketToServer.connect((servers[serverPointer].ip,servers[serverPointer].port))
            #forwarding the data we recieved from client
            socketToServer.send(recv_data)
            message = "Forwarded Message to Server " + str(serverPointer) + "- " + socketToServer.getsockname()[0] + ":" + str(socketToServer.getsockname()[1])
            logging.info(message)
            print(message)
            #getting the response
            recv_data = socketToServer.recv(bufferSize)

            while(recv_data != b''): #while the data is not empty
                
                message = "Recieved Message of size " + str(sys.getsizeof(recv_data)) + " bytes from Server " + str(serverPointer) + "- " + socketToServer.getsockname()[0] + ":" + str(socketToServer.getsockname()[1]) + ":\n" + str(recv_data)
                logging.info(message)
                print(message)
                #sending the message back to the client
                data.outb += recv_data
                sent = sock.send(data.outb)
                data.outb = data.outb[sent:]

                #seeing if theres more data to get
                recv_data = socketToServer.recv(bufferSize) 

            #going to the next server in sequence (Round Robin)
            serverPointer+=1
            if serverPointer == len(servers):
                serverPointer = 0   
        else: #closing connection if done recieving data
            message = 'closing connection to ' + data.addr[0] + ":" + str(data.addr[1])
            logging.info(message)
            print(message)

            #getting rid of socket pretty much
            sel.unregister(sock)
            sock.close()
       
        
             
            
#NO.5 services connection using bySize policy (one with the least data sent so far is next)
#the layout here is almost identical to previous function
def service_connection_bySize(key, mask):
    global servers
    global serverPointer

    sock = key.fileobj
    data = key.data
    if mask & selectors.EVENT_READ:
        recv_data = sock.recv(1024)  # Should be ready to read
        
        if recv_data:
            message = "Recieved Message of size " + str(sys.getsizeof(recv_data)) + "bytes from Client " + data.addr[0] + ":" + str(data.addr[1]) + ":\n" + str(recv_data)
            logging.info(message)
            print(message)
            
            serverPointer = findMinData() #finds socket with min data
            socketToServer = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            socketToServer.connect((servers[serverPointer].ip,servers[serverPointer].port))
            socketToServer.send(recv_data)
            servers[serverPointer].totalData += sys.getsizeof(recv_data)
            message = "Forwarded Message to Server " + str(serverPointer) + "- " + socketToServer.getsockname()[0] + ":" + str(socketToServer.getsockname()[1])
            logging.info(message)
            print(message)
            recv_data = socketToServer.recv(bufferSize)

            while(recv_data != b''): 
                message = "Recieved Message of size " + str(sys.getsizeof(recv_data)) + " bytes from Server " + str(serverPointer) + "- " + socketToServer.getsockname()[0] + ":" + str(socketToServer.getsockname()[1]) + ":\n" + str(recv_data)
                logging.info(message)
                print(message)
                data.outb += recv_data
                recv_data = socketToServer.recv(bufferSize)
                sent = sock.send(data.outb)

                
                data.outb = data.outb[sent:]
            
        else:
            message = 'closing connection to ' + data.addr[0] + ":" + str(data.addr[1])
            logging.info(message)
            print(message)

            sel.unregister(sock)
            sock.close()
       
        

#NO.1 THIS IS WHERE THE PROGRAM STARTS
# python doesnt have a main function, its really stupid      
    
 #sets up logging configuration that goes in logs.log           
logging.basicConfig(filename='logs.log', encoding='utf-8', level=logging.DEBUG, format='%(asctime)s %(message)s', datefmt='%m/%d/%Y %I:%M:%S %p')


#this stuff should be self explanitory, its just getting info from the user
HOST = '127.0.0.1'
PORT = 8000
bufferSize = 1024 * 10

inp = ""
while inp != "RR" and inp != "OS":
    inp = input("Would you like to use Round Robin policy or Output Size Policy? RR/OS\n")
    inp = inp.upper()

useRR = True
if inp == "OS":
    useRR = False

inp = ""
while inp != "Y" and inp != "N":
    inp = input("Would you like to host on a custom port and ip? (Default is localhost:8000) Y/N\n")
    inp = inp.upper()
if  inp == "Y":
    HOST = input("Enter host ip:")
    PORT = int(input("Enter host port:"))
#this selector module is used for multiplexing
sel = selectors.DefaultSelector()
#these 3 lines are for making a socket that acts as a server
lsock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
lsock.bind((HOST, PORT))
lsock.listen()
#whenever you see this logging.info() function, its just adding the text to the log file
logging.info("\n----------------------------------------------------\nSTART")
#i use this message variable so that i can add the message to the log file and print it
message = 'listening on ' + HOST + ":" + str(PORT)
logging.info(message)
print(message)

lsock.setblocking(False)
sel.register(lsock, selectors.EVENT_READ, data=None)
#this is a list (basically a linked list) which can hold any number of SCB(server info)
#IMPORTANT: the port nth of the server is always the host's port + n 
servers = [SCB.SCB(HOST,PORT+1),SCB.SCB(HOST,PORT+2),SCB.SCB(HOST,PORT+3),SCB.SCB(HOST,PORT+4)]
serverPointer = 0 #this variable is the index for which server is in use
while True:
    #the default selector class is doing a lot of the work here, its just selecting which of the connections it has to service next
    events = sel.select(timeout=None)
    for key, mask in events:
        if key.data is None: #this is for accepting new connections
            accept_wrapper(key.fileobj)
        else: #this is for servicing them
            if useRR:
                service_connection_RR(key, mask)
            else:
                service_connection_bySize(key, mask)
            
