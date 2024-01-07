# Author: Nuoxi Zhang
# Date Created: 03/11/2023
import os
import socket
import random
import constants 
import time
class Endpoint:
    def __init__(self, routerAddress : str, destinationAddress : bytes, srcAddress : bytes, isSender : int = 0, bindAddress:str =None) -> None:
        self.address : bytes = srcAddress
        self.address = self.getAddress()
        self.hasReceivedDestinationConfirmation = False
        self.isSender : int = isSender
        self.destinationAddress : bytes = destinationAddress
        self.UDPSocket : socket.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
        # enable broadcasting
        self.UDPSocket.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST,1)
        self.defaultRouterAddress : tuple = (routerAddress, constants.ROUTER_PORT)
        self.bufferSize : int = 65000
        self.UDPSocket.bind(("0.0.0.0", constants.ENDPOINT_PORT))
        self.routerAddress = routerAddress
        print(f"[Endpoint]: List of network interfaces => {self.getListOfNetworks()}\n")
        print(f"[Endpoint]: Up running. Address = {self.address}\n")
   

    def listeningToMessages(self):
        print(f"[Endpoint]: listening to incoming packages\n")
        while True:
            try:
                self.UDPSocket.settimeout(0.05)
                data, address = self.UDPSocket.recvfrom(self.bufferSize)
                ipAddress = address[0]
                frameType : int = int(data[0])
                srcAddress : bytes = data[1:5]
                destinationAddress : bytes = data[5:9]

                if frameType == constants.ROUTING_REQUEST:
                    self.processRoutingRequest(destinationAddress, srcAddress, ipAddress)
                elif frameType == constants.DATA_FRAME:
                    self.processDataPackage(data, srcAddress, ipAddress)
                elif frameType == constants.ACKNOWLEDGEMENT:
                    print(f"[Endpoint]: Received acknowledgement from endpoint {srcAddress}\n")
                elif frameType == constants.DESTINATION_CONFIRMATION_UDP_DATAGRAM:
                    print("Received destination confirmation\n")
                    self.hasReceivedDestinationConfirmation = True
            except socket.timeout:
                pass
            finally:
                self.UDPSocket.settimeout(None)
        


    def sendingMessages(self) -> None:
        
            if self.isSender == 1:
                print("[Endpoint]: Prepare to send data\n")
                self.sendData()
            time.sleep(4)
            if self.isSender == 1:
                self.sendRemoveForwardingTableEntryRequest()

    
    def sendRemoveForwardingTableEntryRequest(self):
        print("[Endpoint]: Sending forward table entry removal request\n")
        header = self.getHeader(self.address, bytearray(b'\x00\x00\x00\x00'), constants.REMOVE_FORWARDING_TABLE_ENTRY)
        message = f"Please remove address {self.address} from your forwarding table".encode("utf-8")
        header.extend(message)
        self.UDPSocket.sendto(header, self.defaultRouterAddress)


        
    def processRoutingRequest(self, destinationAddress : bytes, srcAddress : bytes, ipAddress) -> None:
        print(f"[Endpoint]: Received a routing reqeust looking for destination = {destinationAddress}\n")
        if destinationAddress == self.address:
            print(f"[Endpoint]: I am the destination: {destinationAddress}. Sending a confirmation back\n")
            header : bytearray = self.getHeader(sourceAddress=self.address, destination=srcAddress, type=constants.DESTINATION_CONFIRMATION_UDP_DATAGRAM)
            message : bytes = f"Confirmation from endpoint {self.address}".encode("utf-8")
            header.extend(message)
            self.UDPSocket.sendto(header, (ipAddress, constants.ROUTER_PORT))
            print("[Endpoint]: Confirmation message is sent!\n")
        else:
            print(f"[Endpoint]: I am not the destination wanted. My address is = {self.address}\n")
        
    def processDataPackage(self, data : bytes, srcAddress : bytes, ipAddress) -> None:
        print(f"[Endpoint]: Received data {data if len(data) < 100 else data[:100]} from {srcAddress}\n")
        # send acknowledgement
        header : bytearray = self.getHeader(sourceAddress=self.address, destination=srcAddress, type=constants.ACKNOWLEDGEMENT)
        message : bytes = f"Acknowledgement from endpoint {self.address}".encode("utf-8")
        header.extend(message)
        self.UDPSocket.sendto(header, (ipAddress, constants.ROUTER_PORT))
        print(f"[Endpoint]: Acknowledgement sent to {srcAddress}!\n")
        

    def sendData(self):
        #search for path
        hasPath : bool = self.findAPath() == None
        if(not self.hasReceivedDestinationConfirmation and not hasPath):
            print("[Endpoint]: Destination does not exist.\n")
            return
            
        print("[Endpoint]: Proceed to send data.\n")
        self.sendTextFrame("/compnets/TextFiles/SampleText.txt")
        

    def findAPath(self):
        print(f"[Endpoint]: Sending routing request to default gateway\n")
        message : bytearray = f"This is a message from endpoint {self.address}".encode("utf-8")
        header : bytearray = self.getHeader(self.address, self.destinationAddress)
        header.extend(message)
        #get a new socket instead of using the socket used by the "Listener" thread
        UDPSocket : socket.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
        UDPSocket.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST,1)
        UDPSocket.sendto(header, self.defaultRouterAddress)
        # set time out to 1 second
        UDPSocket.settimeout(1)
        while not self.hasReceivedDestinationConfirmation:
            try:
                data, address = UDPSocket.recvfrom(self.bufferSize)
                print(f"[Endpoint]: Received destination confirmation {data if len(data) < 100 else data[:100]} from address: {address}\n")
                UDPSocket.close()
                return data
            except Exception as e:
                pass
        UDPSocket.close()
        return None
        
        

    def getHeader(self, sourceAddress : bytes, destination : bytearray, type : int = 0) -> bytearray:
        header : bytearray = bytearray()
        header.append(type)
        header.extend(sourceAddress)
        header.extend(destination)
        return header
    
    def convertIPAddressToByteAddress(self, ipAddress : str) -> bytearray:
        byteAddress : bytearray = bytearray()
        startIndex : int = 0
        for endIndex in range(0, len(ipAddress)):
            if ipAddress[endIndex] == '.':
                chunk : int = int(ipAddress[startIndex:endIndex])
                byteAddress.extend(chunk.to_bytes(1, "big"))
                startIndex = endIndex + 1
        # # add last chunk
        chunk : int = int(ipAddress[startIndex:endIndex+1])
        byteAddress.extend(chunk.to_bytes(1, "big"))
        return byteAddress
    
    def getAddress(self) -> bytes:
        interfaces = socket.getaddrinfo(host=socket.gethostname(), port=None, family=socket.AF_INET)
        allips = [ip[-1][0] for ip in interfaces]
        randomAddress : str = allips[random.randrange(0, len(allips))]
        return bytes(self.convertIPAddressToByteAddress(randomAddress))

    def getListOfNetworks(self) -> list[str]:
        listOfNetworks : list[str] = []
        interfaces = socket.getaddrinfo(host=socket.gethostname(), port=None, family=socket.AF_INET)
        allips = [ip[-1][0] for ip in interfaces]
        # randomAddress : str = allips[random.randrange(0, len(allips))]
        for ip in allips:
            if ip not in listOfNetworks:
                listOfNetworks.append(ip)
        return listOfNetworks
    

    def openFileIntoBytes(self, pathToFile : str) -> bytes:
        file = open(pathToFile, "+rb")
        return file.read(os.path.getsize(pathToFile))
    
    def sendTextFrame(self, pathToFile :str) -> None:
        print("Send text\n")
        textInBytes : bytes = self.openFileIntoBytes(pathToFile)
        numberOfChunks = 5
        header = self.getHeader(self.address, self.destinationAddress, constants.DATA_FRAME)
        chunkSize : int = (int) (len(textInBytes) / numberOfChunks)
        currentChunk = 0
        startIndex : int = (int) (currentChunk * chunkSize)
        endIndex : int =(int) (startIndex + chunkSize)

        while endIndex < len(textInBytes):
            chunkToSend : bytes = textInBytes[startIndex:endIndex]
            data = bytearray(header)
            data.extend(chunkToSend)
            print(f"[Endpoint]: Sending text frame: {data if len(data) < 100 else data[:100]}\n")
            self.UDPSocket.sendto(data, self.defaultRouterAddress)
            startIndex = endIndex
            endIndex = endIndex + chunkSize
            time.sleep(2)
        
        
# jsonFilePath = "C://Users//nuoxi//CompNetAssignment//topology.json"