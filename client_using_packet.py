from socket import *
import time
import struct
import os
import sys
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5 import uic

fmt = '=4si'
fmt_size = struct.calcsize(fmt)

FILE_READ_DATA = 1024
HEADER_SIZE = 8

form_class = uic.loadUiType("Chat.ui")[0]

class LoginWindow(QWidget, form_class):
    def __init__(self, sock):
        super().__init__()
        
class WindowClass(QMainWindow, form_class):
    def __init__(self, sock) :
        super().__init__()
        self.setupUi(self)
        self.sock = sock
        self.MessageSendButton.clicked.connect(self.MessageButtonFunction)
        self.FileSendButton.clicked.connect(self.FileButtonFunction)
        
        self.ReceiveThread = Receive(self.sock)
        self.ReceiveThread.ErrorSignal.connect(self.ErrorSignal)
        self.ReceiveThread.MessageSignal.connect(self.MessageSignal)
        self.ReceiveThread.FileSignal.connect(self.FileSignal)
        self.ReceiveThread.start()
        self.FriendsList
        
    def MessageButtonFunction(self):
        try:
            if self.ChatEdit.toPlainText() != '':
                send_data_header = struct.pack(fmt, b'mp00', len(self.ChatEdit.toPlainText().encode('utf-8')))
                self.sock.send(send_data_header + self.ChatEdit.toPlainText().encode('utf-8'))
                self.ChattingList.addItem("나 : " + self.ChatEdit.toPlainText())
                self.ChatEdit.clear()
        except Exception as e:
            print(e)
            self.QMessageBox.critical(self, 'Error', e)
        
    def FileButtonFunction(self):
        try:
            # 파일 경로
            filepath = QFileDialog.getOpenFileName(self, 'Open file', './')
            if filepath != '':
                # 파일 사이즈
                filesize = os.path.getsize(filepath[0])
                # 파일 이름
                filename = os.path.basename(filepath[0]).encode('utf-8')
                # 파일 보낼 경로 수정
                filepath = filepath[0].replace('/', '\\')
                # 파일 전송
                send_data_header = struct.pack(fmt, b'fps0', len(filename))
                self.sock.send(send_data_header + filename)
                
                # 파일 데이터
                with open(filepath, 'rb') as f:
                    while True:
                        print('#', end= '')
                        data = f.read(FILE_READ_DATA)
                        filesize = filesize - FILE_READ_DATA
                        
                        if not data:
                            break
                        
                        if filesize <= 0:
                            send_data_header = struct.pack(fmt, b'fpe0', len(data))
                        else:
                            send_data_header = struct.pack(fmt, b'fpd0', len(data))
                        self.sock.send(send_data_header + data)
                        time.sleep(1)
                    #리스트 뷰에 파일 전송 완료 적기
                    self.ChattingList.addItem("파일 업로드 완료")
        except Exception as e:
            print(e)
            self.QMessageBox.critical(self, 'Error', e)        
    
    @pyqtSlot(str)
    def MessageSignal(self, Message):
        #리스트 뷰에 메세지 올리기
        self.ChattingList.addItem("상대방 : " + Message)
    
    @pyqtSlot(str)
    def FileSignal(self, FileName):        
        self.ChattingList.addItem("상대방 : " + FileName)
    
    @pyqtSlot(str)
    def ErrorSignal(self, Error):
        self.QMessageBox.critical(self, 'Error', Error)
        

class Receive(QThread):
    MessageSignal = pyqtSignal(str)
    FileSignal = pyqtSignal(str)
    ErrorSignal = pyqtSignal(str)
    def __init__(self, sock):
        super().__init__()
        self.sock = sock
        self.AllData = b''
        self.FileName = ''
        self.RECV_FILE_NAME = ''
        self.RECV_FILE_PATH = 'C:/Users/c404/Desktop/sangjin/새 폴더'
    def run(self):
        while True:
            try:
                recv_data_header = self.sock.recv(HEADER_SIZE)
                header = struct.unpack(fmt, recv_data_header)
                recvData = self.sock.recv(header[1])
                
                if header[0][0] == 109:
                    if header[0][1] == 112:
                        self.MessageSignal.emit(recvData.decode())
                        #리스트 뷰에 메세지 넣기
                    elif header[0][1] == 110:
                        self.MessageSignal.emit(recvData.decode())
                        #리스튜 뷰에 메세지 넣기
                elif header[0][0] == 102:
                    if header[0][1] == 112:
                        if header[0][2] == 115:
                            self.RECV_FILE_NAME = recvData.decode()
                        elif header[0][2] == 100:
                            self.AllData += recvData    
                        elif header[0][2] == 101:
                            self.AllData += recvData
                            with open(self.RECV_FILE_PATH + '/' + self.RECV_FILE_NAME, 'wb') as f:
                                f.write(self.AllData)
                                self.RECV_FILE_NAME = ''
                                self.AllData = b''
                                self.FileSignal.emit("파일 다운로드 완료")                        
            except Exception as e:
                print(e)
                self.ErrorSignal.emit(str(e))

port = 8888
if __name__ == "__main__":  
    clientSock = socket(AF_INET, SOCK_STREAM)
    clientSock.connect(('localhost', port))
    app = QApplication(sys.argv)
    myWindow = WindowClass(clientSock)
    myWindow.show()
    app.exec_() 

