# Author: Nuoxi Zhang
from BaseClass.Router import Router
import sys
def main(agrv):
    router : str = agrv[0]
    srcAddress : bytes = None
    if router == 'router1':
        srcAddress = bytes(b'\xab\xcd\xef\x01')
    elif router == "router2":
        srcAddress = bytes(b'\xab\xcd\xef\x02')
    elif router == "router3":
        srcAddress = bytes(b'\xab\xcd\xef\x03')
    else:
        srcAddress = bytes(b'\xab\xcd\xef\x04')



    # print("before initializing router obj\n")
    router : Router = Router(srcAddress)
    # print("after initializing router obj\n")
    router.listeningToAllIncomingRequest()


if __name__ == "__main__":
    main(sys.argv[1:])