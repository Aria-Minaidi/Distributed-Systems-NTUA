# -*- coding: utf-8 -*-
"""
Created on Fri Mar 12 20:25:46 2021

@author: aria_
"""
import time
import socket, random
import threading
import pickle
import sys
import time
import hashlib
import os
from collections import OrderedDict
import pandas as pd
# Default values if command line arguments not given
IP = "192.168.0.3"
PORT = 2000
buffer = 4096
bootstrap=('192.168.0.3',2000)
MAX_BITS = 10        # 10-bit
MAX_NODES = 2 ** MAX_BITS

#replication factor 
k=2
#number of node
num=0
#chain repl
chain=True
# Takes key string, uses SHA-1 hashing and returns a 10-bit (1024) compressed integer
def getHash(key):
    result = hashlib.sha1(key.encode())
    return int(result.hexdigest(), 16) % MAX_NODES

def input():
  return raw_input()

class Node:
    def __init__(self, ip, port):
        self.read_th_start=0
        self.read_th_end=0
        self.filenameList = []
        self.ip = ip
        self.port = port
        self.address = (ip, port)
        self.id = getHash(ip + ":" + str(port))
        self.bootstrap=False
        if (self.address==bootstrap): self.bootstrap=True
        if (self.bootstrap): 
            self.master_dict=dict()
            self.master_dict[self.id]=dict()
            self.filedict=dict()
            self.start_time=0
            self.end_time=0
            self.total_time=0
            self.o=0
        self.pred = (ip, port)            # Predecessor of this node
        self.predID = self.id
        self.succ = (ip, port)            # Successor to this node
        self.succID = self.id
        self.fingerTable = OrderedDict()        # Dictionary: key = IDs and value = (IP, port) tuple
        # Making sockets
            # Server socket used as listening socket for incoming connections hence threaded
        try:
            self.ServerSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.ServerSocket.bind((IP, PORT))
            self.ServerSocket.listen(5)
        except socket.error:
            print("Socket not opened")

    def listenThread(self):
        # Storing the IP and port in address and saving the connection and threading
        while True:
            try:
                connection, address = self.ServerSocket.accept()
                connection.settimeout(120)
                threading.Thread(target=self.connectionThread, args=(connection, address)).start()
            except socket.error:
                pass#print("Error: Connection not accepted. Try again.")

    # Thread for each peer connection
    def connectionThread(self, connection, address):
        rDataList = pickle.loads(connection.recv(buffer))
        #print('PHRA',rDataList)
        # 5 Types of connections
        # type 0: peer connect, type 1: client, type 2: ping, type 3: lookupID, type 4: updateSucc/Pred
        connectionType = rDataList[0]
        if connectionType == 0:
            print("Connection with:", address[0], ":", address[1])
            print("Join network request recevied")
            self.joinNode(connection, address, rDataList)
            #self.printMenu()
        elif connectionType == 1:
            print("Connection with:", address[0], ":", address[1])
            print("Upload/Download request recevied")
            #replicating
            nexT=self.succ
            mpes=rDataList[3]
            last=rDataList[4]
            start_time=rDataList[5]
            sDataList=rDataList
            self.transferFile(connection, address, rDataList)
            if(rDataList[1]==1 or rDataList[1]==2): #an kanei upload h delete
                
                if(mpes==True):     #eimai successor
                    if(chain==False):
                        b = socket.socket(socket.AF_INET, socket.SOCK_STREAM)  #sundesi me bootstrap gia gemisma master dict
                        b.connect(bootstrap)  
                        end=time.time()
                        xronos=end-start_time
                        #print("END-START",xronos)
                        b.sendall(pickle.dumps([21,xronos])) 
                        b.close()     
                    for i in range(k-1):
                        if(last and i==(k-2)):
                            b = socket.socket(socket.AF_INET, socket.SOCK_STREAM)  
                            b.connect(bootstrap)  
                            b.sendall(pickle.dumps([20])) 
                            b.close()
                        
                        sDataList[3]=False
                        s=socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                        s.connect(nexT)
                        s.sendall(pickle.dumps(sDataList))   
                        nexT=pickle.loads(s.recv(buffer))   
                        s.close()
                    #if(k=1)
            
                connection.sendall(pickle.dumps(self.succ))
            #self.transferFile(connection, address, rDataList)
            #self.printMenu()
        elif connectionType == 2:
            #print("Ping recevied ", self.pred)
            connection.sendall(pickle.dumps(self.pred))
        elif connectionType == 3:
            #print("Lookup request recevied")
            self.lookupID(connection, address, rDataList)
        elif connectionType == 4:
            #print("Predecessor/Successor update request recevied")
            if rDataList[1] == 1:
                self.updateSucc(rDataList)
            else:
                self.updatePred(rDataList)
        elif connectionType == 5:
            # print("Update Finger Table request recevied")
            self.updateFTable()
            connection.sendall(pickle.dumps(self.succ))
        elif connectionType == 6:
            connection.sendall(pickle.dumps(self.pred))
        elif connectionType==7:
            connection.sendall(pickle.dumps(self.master_dict))
        elif connectionType==8:
            #newnode=rDataList[1]
            newnodeID=rDataList[1]
            self.master_dict[newnodeID]=dict()
        elif connectionType==9:     #enimerwsi master dict
            newnodeID=rDataList[1]
            self.master_dict[newnodeID]=dict(rDataList[2])
        elif connectionType==10:
            oldnodeID=rDataList[1]
            del self.master_dict[oldnodeID]
        elif connectionType==11:
            connection.sendall(pickle.dumps(self.master_dict))
        elif connectionType==12:
            lista=rDataList[1]
            for item in lista: 
                self.filenameList.remove(item)
            #print('pare ti lista', self.filenameList)
            b = socket.socket(socket.AF_INET, socket.SOCK_STREAM)  #sundesi me bootstrap gia gemisma master dict
            b.connect(bootstrap)  
            sDataList=[9,self.id,self.filenameList]
            b.sendall(pickle.dumps(sDataList))
            b.close()
        elif connectionType==13:
            for item in self.master_dict:
                self.master_dict[item].clear()
        elif connectionType==14:
            file=rDataList[1]
            self.filedict[file[0]]=file[1]  
        elif connectionType==15:
            connection.sendall(pickle.dumps(self.filedict))
        elif connectionType==16:
            filename=rDataList
            del self.filedict[filename]
        elif connectionType==17:
            for item in self.master_dict:
                self.master_dict[item].clear()
            
            for file in self.filedict:
            
                fileID=getHash(file)
                recvIPport = self.getSuccessor(self.succ, fileID)
                self.uploadFile((file,self.filedict[file]), recvIPport, True)      
                
        elif connectionType==18:
            suc=self.succ
            sDataList=suc
            connection.sendall(pickle.dumps(sDataList))
        
        elif connectionType==19:
            self.start_time=time.time()
        
        
        elif connectionType==20:
            self.end_time=time.time()  
            print('Time(needs to be added): ',(self.end_time-self.start_time))

        elif connectionType==21:
            t=rDataList[1]
            self.o+=1
            self.total_time=self.total_time+t
            print('Total Time: ',(self.total_time),self.o)
        
        elif connectionType == 22:  #delete file 
            print("Connection with:", address[0], ":", address[1])
            print("Delete request recevied")
            #replicating
            nexT=self.succ
            mpes=rDataList[3]
            sDataList=rDataList
            if(rDataList[1]==2): #an kanei upload h delete
                if(mpes==True):
                    for i in range(k-1):
                        #print('im in')
                        sDataList[3]=False
                        s=socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                        s.connect(nexT)
                        s.sendall(pickle.dumps(sDataList))   
                        nexT=pickle.loads(s.recv(buffer))   
                        s.close()
            
                connection.sendall(pickle.dumps(self.succ))
            self.transferFile(connection, address, rDataList)
            
        else:
            print("Problem with connection type")
        #connection.close()
    
    # Deals with join network request by other node
    def joinNode(self, connection, address, rDataList):
        if rDataList:
            peerIPport = rDataList[1]
            peerID = getHash(peerIPport[0] + ":" + str(peerIPport[1]))
            oldPred = self.pred
            # Updating pred
            self.pred = peerIPport
            self.predID = peerID
            # Sending new peer's pred back to it
            sDataList = [oldPred]
            connection.sendall(pickle.dumps(sDataList))
            #Updating F table
            time.sleep(0.1)
            self.updateFTable()
            # Then asking other peers to update their f table as well
            self.updateOtherFTables()
            #empty mdict
            b = socket.socket(socket.AF_INET, socket.SOCK_STREAM)  #empty master dict
            b.connect(bootstrap)  
            sDataList=[13]
            b.sendall(pickle.dumps(sDataList))
            b.close()    
            
            #get filedict
            b = socket.socket(socket.AF_INET, socket.SOCK_STREAM)  #empty master dict
            b.connect(bootstrap)  
            sDataList=[15]
            b.sendall(pickle.dumps(sDataList))
            filedict=pickle.loads(b.recv(buffer))    
            b.close()     
        

            for file in filedict:
                
                fileID=getHash(file)
                recvIPport = self.getSuccessor(self.succ, fileID)
                #print('SUCCESSOOOOOOOOR', self.succ)
                self.uploadFile((file,filedict[file]), recvIPport, True)
  

    def transferFile(self, connection, address, rDataList):
        # Choice: 0 = download, 1 = upload
        choice = rDataList[1]
        filename = rDataList[2]
        #print('FILENAME',filename)
        fileID = getHash(filename[0])      #to file einai toupla 
        # IF client wants to download file
        if choice == 0:
            print("Download request for file:", filename)
            try:
                dictionary=dict(self.filenameList)
                # First it searches its own directory (fileIDList). If not found, send does not exist
                if filename not in dictionary.keys():
                    msg='NotFound'
                    print("File not found")
                    connection.sendall(pickle.dumps(msg))
                else:   # If file exists in its directory   # Sending DATA LIST Structure (sDataList):
                    #connection.send("Found".encode('utf-8'))
                    self.sendFile(connection, [filename,dictionary[filename]])
            except ConnectionResetError as error:
                print(error, "\nClient disconnected\n\n")
        # ELSE IF client wants to upload something to network
        elif choice == 1 or choice == -1:
            print("Receiving file:", filename)
            fileID = getHash(filename[0])
            print("Uploading file ID:", fileID)
            self.filenameList.append(filename)
            
            b = socket.socket(socket.AF_INET, socket.SOCK_STREAM)  #sundesi me bootstrap gia gemisma master dict
            b.connect(bootstrap)  
            sDataList=[9,self.id,self.filenameList]
            b.sendall(pickle.dumps(sDataList))
            #self.receiveFile(connection, filename)
            print("Upload complete")
            # Replicating file to successor as well
            #if choice == 1:
            #    if self.address != self.succ:
            #        self.uploadFile(filename, self.succ, False)
        elif choice==2:     #delete file
            try:
                dictionary=dict(self.filenameList)
                # First it searches its own directory (fileIDList). If not found, send does not exist
                if filename not in dictionary.keys():
                    connection.sendall(pickle.dumps("NotFound"))
                    print("File not found")
                else:   # If file exists in its directory   # Sending DATA LIST Structure (sDataList):
                    del dictionary[filename]
                    #print(self.filenameList, 'ctdd', dictionary)
                    self.filenameList=list(dictionary.items()) 
                    #print("listara", self.filenameList)
                    #connection.sendall(pickle.dumps('OK'))
                    b = socket.socket(socket.AF_INET, socket.SOCK_STREAM)  #sundesi me bootstrap gia gemisma master dict
                    b.connect(bootstrap)  
                    sDataList=[9,self.id,self.filenameList]
                    b.sendall(pickle.dumps(sDataList))   
                    print("File is deleted")
            except ConnectionResetError as error:
                print(error, "\nClient disconnected\n\n")
            

    def lookupID(self, connection, address, rDataList):
        keyID = rDataList[1]
        sDataList = []
        #print("pred  self succ key ID's", self.predID, self.id, self.succID, keyID)

        if self.id == keyID:        
            sDataList = [0, self.address]
            
        
        elif self.succID == keyID:
            sDataList = [0, self.succ]
            

        elif self.predID == keyID:
            sDataList = [0, self.pred]

        elif self.succID == self.id:  
            sDataList = [0, self.address]
            

        elif self.id < keyID <= self.succID:
            sDataList = [0, self.succ]
        
         
        elif self.predID < keyID <= self.id:
            sDataList = [0, self.address]
        

        elif self.predID < keyID and self.id < self.predID:
            sDataList = [0, self.address] 
            

        elif self.id > keyID and self.id < self.predID:
            sDataList = [0, self.address] 
            
        
        elif self.id < keyID and self.succID < self.id:
            sDataList = [0, self.succ] 
           
        
        elif self.id > keyID and self.succID < self.id:
            sDataList = [0, self.succ] 
            

        elif self.id > keyID:  
            
            value = ()
            for key, value in self.fingerTable.items():
                if key <= keyID:
                    break
                value=value
            sDataList = [1, value[1]]

        elif self.id < keyID:  
            #print("i")         
            value = ()
            #print("fingertable  ", self.fingerTable.items())
            for key, value in self.fingerTable.items():
                if key >= keyID:
                    break
                value=value   
            if(len(value)!=2):
                value=(0,self.succ)
            sDataList = [1, value[1]]
                
        connection.sendall(pickle.dumps(sDataList))
        #print(sDataList)

    def updateSucc(self, rDataList):
        newSucc = rDataList[2]
        self.succ = newSucc
        self.succID = getHash(newSucc[0] + ":" + str(newSucc[1]))
        # print("Updated succ to", self.succID)
    
    def updatePred(self, rDataList):
        newPred = rDataList[2]
        self.pred = newPred
        self.predID = getHash(newPred[0] + ":" + str(newPred[1]))
        # print("Updated pred to", self.predID)

    def start(self):
        # Accepting connections from other threads
        threading.Thread(target=self.listenThread, args=()).start()
        #threading.Thread(target=self.pingSucc, args=()).start()
        # In case of connecting to other clients
        while True:
            print("Listening to other clients")   
            self.asAClientThread()
    


    # Handles all outgoing connections
    def asAClientThread(self):
        # Printing options
        
        userChoice = input()
        if userChoice == "join":
            self.sendJoinRequest(bootstrap[0], bootstrap[1])
            
        elif userChoice == "depart":
            self.leaveNetwork()
            
        elif userChoice == "insert": 
            print("Enter filename: ")
            filename = input()
            filename = filename.split(', ')
            fileID = getHash(filename[0])
            filename=(filename[0],filename[1])
            recvIPport = self.getSuccessor(self.succ, fileID)
            self.uploadFile(filename, recvIPport, False)
            
        elif userChoice == "query":
            print("Enter filename: ")
            filename = input()
            if (filename=='*'):
                sDataList=[7]
                boot = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                boot.connect(bootstrap)
                boot.sendall(pickle.dumps(sDataList))
                
                ddd=pickle.loads(boot.recv(buffer))
                print('DHT Files: ',ddd)
            #self.sendFile(cSocket, filename)
            else:
                
                self.downloadFile(filename)
        elif userChoice == "FTable":
            self.printFTable()
            
        elif userChoice == "succ/pred":
            print("My ID:", self.id, "Predecessor:", self.predID, "Successor:", self.succID)
            
        elif userChoice == "delete":         #delete file
            print("Enter filename: ")
            filename = input()
            self.deleteFile(filename)
            
        elif userChoice == "help":         
            self.helpMenu()
            
        elif userChoice == "read_insert":
            
            df=pd.read_csv(str(num)+'ins.txt',header=None)
            last=False
            for i in range(len(df)):
                filename=[None,None]
                filename[0]=df.iloc[i,0]
                filename[1]=df.iloc[i,1]
                fileID = getHash(filename[0])
                filename=(filename[0],filename[1])
                recvIPport = self.getSuccessor(self.succ, fileID)
                if (i==0 and chain):
                    b = socket.socket(socket.AF_INET, socket.SOCK_STREAM)  
                    b.connect(bootstrap)  
                    sDataList=[19]
                    b.sendall(pickle.dumps(sDataList))
                    b.close()
                if(i==(len(df)-1) and chain):
                    last=True                
                if(chain==False):
                    start_time=time.time()
                else:
                    start_time=0
                    
                self.uploadFile(filename, recvIPport, False, last,start_time)
        elif userChoice == "read_query":
            df=pd.read_csv(str(num)+'quer.txt',header=None)
            last=False
            # df=df.apply(lambda x: x.str.replace(' ',''))
            for i in range(len(df)):
                filename = str(df[0][i])
                if(i==(len(df)-1)):
                    last=True
                if (filename=='*'):
                    sDataList=[7]
                    boot = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                    boot.connect(bootstrap)
                    boot.sendall(pickle.dumps(sDataList))
                    
                    ddd=pickle.loads(boot.recv(buffer))
                    print('DHT Files: ',ddd)
                #self.sendFile(cSocket, filename)
                else:
                    self.read_th_start=time.time()
                    self.downloadFile(filename,last)
        elif userChoice == "read_requests":
            df=pd.read_csv(str(num)+'req.txt',header=None)
            for i in range(len(df)):
                if df[0][i]=='insert':
                    filename=[None,None]
                    filename[0]=df.iloc[i,1]
                    filename[1]=df.iloc[i,2]
                    fileID = getHash(filename[0])
                    filename=(filename[0],filename[1])
                    recvIPport = self.getSuccessor(self.succ, fileID)
                    self.uploadFile(filename, recvIPport, False)
                elif df[0][i]=='query':
                    # df[1][i]=df[1][i].apply(lambda x: x.str.replace(' ',''))
                    filename = str(df[1][i])
                    if (filename=='*'):
                        sDataList=[7]
                        boot = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                        boot.connect(bootstrap)
                        boot.sendall(pickle.dumps(sDataList))
                        
                        ddd=pickle.loads(boot.recv(buffer))
                        print('DHT Files: ',ddd)
                    #self.sendFile(cSocket, filename)
                    else:
                        self.downloadFile(filename)
        elif userChoice == "overlay":
            #self.printFTable()
            sDataList=[11]
            boot = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            boot.connect(bootstrap)
            boot.sendall(pickle.dumps(sDataList))     
            ddd=pickle.loads(boot.recv(buffer))
            print('Printing Nodes in Order: \n')
            for key, value in sorted(ddd.items(), key=lambda x: x[0]): 
                print("Node {}".format(key))       
           
        
        
     

    def sendJoinRequest(self, ip, port):    #karfwmena tou bootstrap
        try:
            recvIPPort = self.getSuccessor((ip, port), self.id)     #SYNDESI ME SUCCESSOR BOOTSTRAP
            
            peerSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            peerSocket.connect(recvIPPort)              
            sDataList = [0, self.address]
            
            peerSocket.sendall(pickle.dumps(sDataList))     # Sending self peer address to add to network
            rDataList = pickle.loads(peerSocket.recv(buffer))   # Receiving new pred
            # Updating pred and succ
            
            self.pred = rDataList[0]
            self.predID = getHash(self.pred[0] + ":" + str(self.pred[1]))
            self.succ = recvIPPort
            self.succID = getHash(recvIPPort[0] + ":" + str(recvIPPort[1]))
            # Tell pred to update its successor which is now me
            sDataList = [4, 1, self.address]
            pSocket2 = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            pSocket2.connect(self.pred)
            pSocket2.sendall(pickle.dumps(sDataList))
            pSocket2.close()
            peerSocket.close()

            
            b = socket.socket(socket.AF_INET, socket.SOCK_STREAM)  
            b.connect(bootstrap)  
            sDataList=[9,self.id,self.filenameList]
            b.sendall(pickle.dumps(sDataList))
            b.close()
            

  
        except socket.error:
            print("Socket error. Recheck IP/Port.")
    
    def leaveNetwork(self):
        #First inform my succ to update its pred
        pSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        pSocket.connect(self.succ)
        pSocket.sendall(pickle.dumps([4, 0, self.pred]))
        pSocket.close()
        # Then inform my pred to update its succ
        pSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        pSocket.connect(self.pred)
        pSocket.sendall(pickle.dumps([4, 1, self.succ]))
        pSocket.close()

        b = socket.socket(socket.AF_INET, socket.SOCK_STREAM)  #sundesi me bootstrap gia delete my master dict node
        b.connect(bootstrap)  
        sDataList=[10,self.id]
        b.sendall(pickle.dumps(sDataList))
        b.close()
        
        self.updateOtherFTables()   # Telling others to update their f tables
        
        self.pred = (self.ip, self.port)    # Chaning the pointers to default
        self.predID = self.id
        self.succ = (self.ip, self.port)
        self.succID = self.id
        self.fingerTable.clear()
        print(self.address, "has left the network")
        
        #call mama
        b = socket.socket(socket.AF_INET, socket.SOCK_STREAM)  #sundesi me bootstrap gia delete my master dict node
        b.connect(bootstrap)  
        sDataList=[17]
        b.sendall(pickle.dumps(sDataList))
        b.close()
           
    
    def deleteFile(self, filename):
        print("Deleting file", filename)
        
        # If not found send lookup request to get peer to upload file
        fileID = getHash(filename)
        print('fileID ',fileID)
        
        #update filedict
        b = socket.socket(socket.AF_INET, socket.SOCK_STREAM)  #sundesi me bootstrap gia gemisma master dict
        b.connect(bootstrap)  
        sDataList=[16,filename]
        b.sendall(pickle.dumps(sDataList))       
        b.close()
       
        # First finding node with the file
        recvIPport = self.getSuccessor(self.succ, fileID)
        #print('successor:',recvIPport)

        sDataList = [22, 2, filename]
        
        cSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        cSocket.connect(recvIPport)
        sDataList.append(True)
        cSocket.sendall(pickle.dumps(sDataList))      

        print('deleted')
        

        
     
    
    def uploadFile(self, filename, recvIPport, replicate, last=False,start_time=0):
        print("Uploading file", filename)
        # If not found send lookup request to get peer to upload file
        #update FILEDICT 
        b = socket.socket(socket.AF_INET, socket.SOCK_STREAM)  
        b.connect(bootstrap)  
        sDataList=[14,filename]
        b.sendall(pickle.dumps(sDataList))
        b.close()
        
        
        
        sDataList = [1]
        if replicate:
            sDataList.append(1)
        else:
            sDataList.append(1)
        try:
            sDataList = sDataList + [filename]
            sDataList.append(True)  #mpes
            sDataList=sDataList+[last,start_time]           
            
            cSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            cSocket.connect(recvIPport)
            cSocket.sendall(pickle.dumps(sDataList))
          
            cSocket.close()

                
            print("File uploaded")

        except IOError:
            print("File not in directory")
        except socket.error:
            print("Error in uploading file")
    
    def downloadFile(self, filename,last=False):
        print("Downloading file", filename)
        fileID = getHash(filename)
        print('fileID ',fileID)
        # First finding node with the file



        if chain==True:
            ne=self.succ
            kDataList=[18]
            for i in range(k-1):
                x=socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                x.connect(ne)
                x.sendall(pickle.dumps(kDataList))   
                ne=pickle.loads(x.recv(buffer))   
                x.close()                                 
            recvIPport = ne
        
        else:
            recvIPport = self.succ#self.getSuccessor(self.succ, fileID)
        
        
        
        
        #recvIPport = self.getSuccessor(self.succ, fileID)
             
        #print('successor:',recvIPport)

        sDataList = [1, 0, filename,None,None,None]
        
        cSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        cSocket.connect(recvIPport)
        cSocket.sendall(pickle.dumps(sDataList))      
        # Receiving confirmation if file found or not
        
        fileData=pickle.loads(cSocket.recv(buffer))     
        self.read_th_end=time.time()
        if last:
            print('TIME: ', (self.read_th_end-self.read_th_start))


        if fileData == "NotFound": 
            print("File not found in Succ: ", filename)

        else:
            print("Receiving file:", filename)
            print('The value of the file is:',fileData[0][1])
            print("Got the file from: ",fileData[1])

        
        

    def getSuccessor(self, address, keyID):
        rDataList = [1, address]      # Deafult values to run while loop
        recvIPPort = rDataList[1]
        while rDataList[0] == 1 :
            peerSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            try:
                peerSocket.connect(recvIPPort)
                # Send continous lookup requests until required peer ID
                sDataList = [3, keyID]
                peerSocket.sendall(pickle.dumps(sDataList))
                # Do continous lookup until you get your postion (0)
                rDataList = pickle.loads(peerSocket.recv(buffer))
                recvIPPort = rDataList[1]
                peerSocket.close()
                #print("akshat")
            except socket.error:
                print("Connection denied while getting Successor")
                break
                
        # print(rDataList)
        return recvIPPort
    
    def updateFTable(self):
        for i in range(MAX_BITS):
            entryId = (self.id + (2 ** i)) % MAX_NODES
            # If only one node in network
            if self.succ == self.address:
                self.fingerTable[entryId] = (self.id, self.address)
                continue
            # If multiple nodes in network, we find succ for each entryID
            recvIPPort = self.getSuccessor(self.succ, entryId)
            recvId = getHash(recvIPPort[0] + ":" + str(recvIPPort[1]))
            self.fingerTable[entryId] = (recvId, recvIPPort)
        # self.printFTable()
    
    def updateOtherFTables(self):
        here = self.succ
        while True:
            if here == self.address:
                break
            pSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            try:
                pSocket.connect(here)  # Connecting to server
                pSocket.sendall(pickle.dumps([5]))
                here = pickle.loads(pSocket.recv(buffer))
                pSocket.close()
                if here == self.succ:
                    break
            except socket.error:
                print("Connection denied")

    def sendFile(self, connection,filename):
        print("Sending file:", filename)     
        connection.sendall(pickle.dumps([filename,self.address]))

        print("File sent")

    def printMenu(self):
        
        print("\n-join- Join Network \n-depart- Leave Network \n-insert-  Insert <key>, <value> \n-query- Query <key> (special case * prints every key,value on DHT)")
        print("-succ/pred- Prints ID,succesor,predecessor of given node")
        print("-delete- Delete <key> \n-overlay- Print Network topology \n-read_insert- Execute insert.txt \n-read_query- Execute insert.txt \n-read_requests- Execute requests.txt  ")
        
        
    def helpMenu(self):
        print("\n-join- Join Network(auto connect to bootsrap node) \n-depart- Exits from network's topology \n-insert-  Insert <key>, <value> (for example 'ntua, 1') \n-query- Query <key> (special case * prints every key,value on DHT)")
        print("-delete- Delete <key> from DHT network \n-overlay- Print Network topology as ordered nodes \n-read_insert- Execute insert.txt for given node \n-read_query- Execute query.txt for given node \n-read_requests- Execute requests.txt for given node ")
        print("-succ/pred- Prints ID,succesor,predecessor of given node")
    def printFTable(self):
        print("Printing F Table")
        for key, value in self.fingerTable.items(): 
            print("KeyID:", key, "Value", value)

if len(sys.argv) < 3:
    print("Arguments not supplied (Defaults used)")
else:
    IP = sys.argv[1]
    PORT = int(sys.argv[2])

myNode = Node(IP, PORT)
print("My ID is:", myNode.id)
myNode.start()
myNode.ServerSocket.close()