import os

def check_sits(hostName):
 
    response = os.system("ping -n 1 " + hostName)
    
    if response == 0:
    
        Netstatus = "Network Active"
        
    else:
    
        Netstatus = "Network Error"
 
    return Netstatus
 
 
if __name__ == "__main__":
 
    ret=check_sits('8.8.8.8')
    
    print(ret)

    if ret == "Network Error":
        os.system('shutdown -r now')