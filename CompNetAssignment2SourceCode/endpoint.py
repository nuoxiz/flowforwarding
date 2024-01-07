# Author: Nuoxi Zhang
from BaseClass.Endpoint import Endpoint
import sys
import threading
def main(argv):
    epoint : str = argv[2]
    sourceAddress : bytes = None
    if epoint == "endpoint1":
        sourceAddress = bytes(b'\xef\xcd\xab\x01')
    elif epoint == 'endpoint2':
        sourceAddress = bytes(b'\xef\xcd\xab\x02')
    elif epoint == 'endpoint3':
        sourceAddress = bytes(b'\xef\xcd\xab\x03')
    else:
        sourceAddress = bytes(b'\xef\xcd\xab\x04')
    
    destinationAddress : bytes = bytes(b'\xc0\xa8\n\x03')
    if epoint == 'endpoint4':
        destinationAddress = bytes(b'\xc0\xa8\n\x04')


    endpoint : Endpoint = Endpoint(argv[0], destinationAddress, sourceAddress, int(argv[1]), argv[2])


    thread1 = threading.Thread(target=endpoint.listeningToMessages)
    thread2 = threading.Thread(target=endpoint.sendingMessages)
    thread1.start()
    thread2.start()
    




if __name__ == "__main__":
    main(sys.argv[1:])