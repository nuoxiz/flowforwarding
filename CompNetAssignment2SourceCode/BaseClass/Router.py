# Author: Nuoxi Zhang
# Date Created: 03/11/2023
import datetime
import socket
import constants
import random
class Router:
    def __init__(self, selfAddress : bytes) -> None:
        self.bufferSize : int = 65000
        self.listOfNetworks : list[str] = []
        self.address = self.getAttachedNetworkAddress()
        self.forwardingTable : dict[bytes, list] = {}
        # self.listOfNetworks : list[str] = []
        self.addressToIpMap : dict[str, bytes] = {}
        self.requestTable : dict[bytes, list] = {}
        self.aliveTimeInSeconds : int = 30

        # set up the sockets
        self.GeneralPurposeSocket : socket.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
        self.GeneralPurposeSocket.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        self.GeneralPurposeSocket.bind(("0.0.0.0", constants.ROUTER_PORT))

        self.getAttachedNetworkAddress()
        print(f"[Router]: Router started. List of network interface: {self.listOfNetworks}, Address = {self.address}\n")

    def listeningToAllIncomingRequest(self):
        print(f"[Router]: Listening to incoming messages\n")
        while True:
            try:
                self.GeneralPurposeSocket.settimeout(1)
                data, ipAddress = self.GeneralPurposeSocket.recvfrom(self.bufferSize)
                print(f"[Router]: Forward table => {self.forwardingTable}\n")
                # print(f"IP Address pair => {ipAddress}\n")
                data = bytearray(data)
                print(f"[Router]: Received data: {data if len(data) < 100 else data[:100]} from IP Address: {ipAddress[0]}\n")
                frameType : int = int(data[0])
                sourceAddress : bytes = bytes(data[1:5])
                destinationAddress : bytes = bytes(data[5:9])
                if ipAddress[0] in self.listOfNetworks:
                    print("[Router]: This is a broadcast from myself, skip this message\n")
                    continue
                else:
                    if frameType == constants.ROUTING_REQUEST:
                        print(f"[Router]: This is a Routing request from {sourceAddress} to {destinationAddress}. Proceed to broadcast\n")
                        # add to forwarding table
                        if sourceAddress not in self.forwardingTable:
                            self.forwardingTable[sourceAddress] = [sourceAddress, ipAddress[0], self.getCurrentTimeAsInteger()]
                        else:
                            self.forwardingTable[sourceAddress][2] = self.getCurrentTimeAsInteger()

                        

                        if destinationAddress not in self.forwardingTable:
                            print(f"[Router]: ------------------> Destionation address: {destinationAddress} is not in the forward table\n")
                            self.broadcastRequest(data, ipAddress[0])
                        else:
                            print(f"[Router]: ------------------> Destionation address: {destinationAddress} is in the forward table\n")
                            self.sendRoutingConfirmation(sourceAddress, destinationAddress, ipAddress)
                        

                    elif frameType == constants.DESTINATION_CONFIRMATION_UDP_DATAGRAM:
                        print(f"[Router]: This is a Destination Confirmation from {sourceAddress} to {destinationAddress}\n")
                        if sourceAddress not in self.forwardingTable:
                            self.forwardingTable[sourceAddress] = [sourceAddress, ipAddress[0], self.getCurrentTimeAsInteger()]
                        else:
                            self.forwardingTable[sourceAddress][2] = self.getCurrentTimeAsInteger()
                            # self.forwardingTable[destinationAddress][2] = self.getCurrentTimeAsInteger()
                        # get next hop IP Address
                        nextHopAddress : str = self.forwardingTable[destinationAddress][1]
                        print(f"[Router]: This is a Destination Confirmation from {sourceAddress} to {destinationAddress}. IP Address for next hop:  {nextHopAddress}\n")
                        # iterate through the list of networks
                        for connectedIPAddress in self.listOfNetworks:
                            # find the IP address which is in the same network as "nextHopAddress"
                            if not self.isSendingAddress(connectedIPAddress, nextHopAddress):
                                sock : socket.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
                                # bind to the IP address that is in the same network as "nextHopAddress"
                                sock.bind((connectedIPAddress, 0))
                                # forward the ACK to the "nextHopaddress", could be another router or the destination endpoint
                                sock.sendto(data, (nextHopAddress, constants.ROUTER_PORT))
                                print(f"[Endpoint]: Destination Confirmation is forwarded to next hop: {nextHopAddress} from current IP address: {connectedIPAddress}\n")
                                sock.close()
                    
                    elif frameType == constants.DATA_FRAME:
                        if sourceAddress not in self.forwardingTable:
                            self.forwardingTable[sourceAddress] = [sourceAddress, ipAddress[0], self.getCurrentTimeAsInteger()]
                        else:
                            self.forwardingTable[sourceAddress][2] = self.getCurrentTimeAsInteger()
                            self.forwardingTable[destinationAddress][2] = self.getCurrentTimeAsInteger()
                        
                        # if sourceAddress not in self.forwardingTable:
                        #     self.forwardingTable[sourceAddress] = [sourceAddress, ipAddress[0], self.getCurrentTimeAsInteger()]
                        # else:
                        #     self.forwardingTable[sourceAddress][2] = self.getCurrentTimeAsInteger()

                        nextHopAddress : str = self.forwardingTable[destinationAddress][1]
                        print(f"[Router]: This is a Data Frame from {sourceAddress} to {destinationAddress}\nIP Address for next hop:  {nextHopAddress}\n")
                        for connectedIPAddress in self.listOfNetworks:
                            # find the ip address that belongs to the network from which the
                            # original routing request is from
                            if not self.isSendingAddress(connectedIPAddress, nextHopAddress):
                                sock : socket.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
                                sock.bind((connectedIPAddress, constants.ROUTER_PORT + 1))
                                sock.sendto(data, (nextHopAddress, constants.ROUTER_PORT))
                                print(f"[Endpoint]: Data Frame forwarded to next hop: {nextHopAddress} from {connectedIPAddress}\n")
                                sock.close()
                    elif frameType == constants.ACKNOWLEDGEMENT:
                        if sourceAddress not in self.forwardingTable:
                            self.forwardingTable[sourceAddress] = [sourceAddress, ipAddress[0], self.getCurrentTimeAsInteger()]
                        else:
                            self.forwardingTable[sourceAddress][2] = self.getCurrentTimeAsInteger()
                            self.forwardingTable[destinationAddress][2] = self.getCurrentTimeAsInteger()
                        nextHopAddress : str = self.forwardingTable[destinationAddress][1]
                        print(f"[Router]: This is an ACK from {sourceAddress} to {destinationAddress}\nIP Address for next hop: {nextHopAddress}    \n")
                        for connectedIPAddress in self.listOfNetworks:
                            # find the ip address that belongs to the network from which the
                            # original routing request is from
                            if not self.isSendingAddress(connectedIPAddress, nextHopAddress):
                                sock : socket.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
                                sock.bind((connectedIPAddress, constants.ROUTER_PORT + 1))
                                sock.sendto(data, (nextHopAddress, constants.ROUTER_PORT))
                                print(f"[Endpoint]: ACK sent to next hop: {nextHopAddress} from {connectedIPAddress}\n")
                                sock.close()
                    elif frameType == constants.REMOVE_FORWARDING_TABLE_ENTRY:
                        print(f"[Router]: -------------> Received removal request from {sourceAddress}\n")
                        print(f"[Router]: -------------> Forward table before deletion {self.forwardingTable}\n")
                        # remove entry from forwarding table
                        if self.forwardingTable.get(sourceAddress):
                            print("[Router]: Forwarding table entry deleted\n")
                            del self.forwardingTable[sourceAddress]

                        print(f"[Router]: -------------> Forward table after deletion: {self.forwardingTable}\n")
                        # broadcast to all
                        print(f"[Router]: Broadcast Forward table entry removal request\n")
                        self.broadcastRequest(data, ipAddress[0])
            except TimeoutError as e:
                pass
            finally:
                self.cleanOutdatedEntry()
                    

    def sendRoutingConfirmation(self, sourceAddress : bytes, destionationAddress : bytes, sourceIPAddressAndPortNumber) -> None:
        print("[Router]: ----------------> Send routing confirmation \n")
        header = self.getHeader(destionationAddress, sourceAddress, constants.DESTINATION_CONFIRMATION_UDP_DATAGRAM)
        message = f"[Router]: Confirmation of the location of {destionationAddress} from Router {self.address}".encode("utf-8")
        header.extend(message)
        for ipAddress in self.listOfNetworks:
            if not self.isSendingAddress(ipAddress, sourceIPAddressAndPortNumber[0]):
                print(f"Router -------------> Sending confirmation on {ipAddress}\n")
                self.GeneralPurposeSocket.sendto(header, (sourceIPAddressAndPortNumber))
                print("----------------> Routing confirmation sent -------------------------\n")    


    def isSendingAddress(self, ipAddress : str, srcIpAddress : str) -> bool:
        numberOfDotsEncountered : int = 0
        index : int = 0
        while numberOfDotsEncountered < 3:
            if ipAddress[index] != srcIpAddress[index]:
                return True
            if ipAddress[index] == '.':
                numberOfDotsEncountered = numberOfDotsEncountered + 1
            index = index + 1
        return False
    
    def broadcastRequest(self, data:bytearray, srcIpAddress : str):
        print(f"[Endpoint]: Broadcasting message = {data if len(data) < 100 else data[:100]}\n")
        index = 0
        for ipAddress in self.listOfNetworks:
            if self.isSendingAddress(ipAddress, srcIpAddress):
                print(f"[Endpoint]: Sending on {ipAddress}, broadcasting address = {self.getBroadcastAddress(ipAddress)}\n")
                sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)  # UDP
                sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
                sock.bind((ipAddress,0))
                sock.sendto(data, (self.getBroadcastAddress(ipAddress), constants.ROUTER_PORT))
                index = index + 1
                sock.close()
        if index == 0:
            print(f"[Endpoint]: Not connected to other network except the one from which the routing request is from\n")

    def getBroadcastAddress(self, ipAddress : str, subnet : int = 24) -> str:
        index : int = len(ipAddress) - 1
        while(ipAddress[index] != '.'):
            index = index - 1
            broadcastAddress : str = ipAddress[0:index + 1] + "255"
        return broadcastAddress

    def getCurrentTimeAsInteger(self) -> int:
        now = datetime.datetime.now()
        date_string = now.strftime("%d%H%M%S")
        date_int = int(date_string)
        return date_int
            
    def getHeader(self, sourceAddress : bytes, destinationAddress : bytes, type : int ) -> bytearray:
        header : bytearray = bytearray()
        header.append(type)
        header.extend(sourceAddress)
        header.extend(destinationAddress)
        return header

    def cleanOutdatedEntry(self) -> None:
        currentTime : int = self.getCurrentTimeAsInteger()
        for address in list(self.forwardingTable):
            entry : list = self.forwardingTable[address]
            recordedTimestamp : int = entry[2]
            # if the entry is outdated
            if( currentTime - recordedTimestamp >= self.aliveTimeInSeconds ):
                print(f"[Router]: Current Time: {currentTime}\n")
                print(f"[Router]: Entry => {entry} has became outdated. Preparing to remove it.\n")
                # delete outdated entry
                del self.forwardingTable[address]
    
    def convertIPAddressToByteAddress(self, ipAddress : str) -> bytearray:
        # example: ipAddress = 192.168.20.3
        byteAddress : bytearray = bytearray()
        startIndex : int = 0
        # iterate through each character in the IP address
        for endIndex in range(0, len(ipAddress)):
            if ipAddress[endIndex] == '.':
                # extrac the chunk of ipAddress, e.g. 192 is the first chunk 
                chunk : int = int(ipAddress[startIndex:endIndex])
                # convert the chunk to hexadecimal form and append to the answer
                byteAddress.extend(chunk.to_bytes(1, "big"))
                startIndex = endIndex + 1
        # add last chunk
        chunk : int = int(ipAddress[startIndex:endIndex+1])
        byteAddress.extend(chunk.to_bytes(1, "big"))
        # return the 4-bytes address
        return byteAddress
    def getAttachedNetworkAddress(self) -> bytes:
        # get all the network interface(s) the network element is connected to
        interfaces = socket.getaddrinfo(host=socket.gethostname(), port=None, family=socket.AF_INET)
        # Convert to a list of IPv4 addresses, which could contain duplicate
        allips = [ip[-1][0] for ip in interfaces]
        for ip in allips:
            if ip not in self.listOfNetworks:
                # only record each IPv4 address once.
                self.listOfNetworks.append(ip)
        # randomly select an IP address and convert it to the 4-bytes address
        randomIndex : int = random.randrange(0, len(self.listOfNetworks))
        return self.convertIPAddressToByteAddress(self.listOfNetworks[randomIndex])
