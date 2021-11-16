import socket

class Server():
  def __init__(self,Adress=('',5000),MaxClient=1):
      self.s = socket.socket()
      self.s.bind(Adress)
      self.s.listen(MaxClient)


s = Server()
(clientConnected, clientAddress) = s.s.accept()

print("Accepted a connection request from %s:%s" % (clientAddress[0], clientAddress[1]))
while True:
    dataFromClient = clientConnected.recv(1024)
    print(dataFromClient.decode())

