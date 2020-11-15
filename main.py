import socket
from cv2 import cv2
import pickle
from zlib import compress
from zlib import decompress
import tkinter as tk
BUFF_SIZE=1024
HOST="127.0.0.1"
PORT=20206
remote=(HOST,PORT)
def click_c():
    # 发送端
    def as_client():
        HOST=entrytext.get()
        remote=(HOST,PORT)
        def release():
            # release all
            cv2.destroyAllWindows()
            video_capture.release()
            c_socket.close()
            exit()
        # 建立 UDP 套接字，并与本机 IP 地址绑定
        c_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        c_socket.bind(('',PORT))
        # 建立视频捕获实例
        video_capture = cv2.VideoCapture(0)
        while video_capture.isOpened():
            # Capture a frame
            ret, frame = video_capture.read()
            # 将视频帧转换为字节类型并压缩
            framez=compress(pickle.dumps(frame),1)
            # 根据帧大小和接收缓冲区大小计算每一帧拆分的个数
            sizefz=framez.__len__()
            packnum=int(sizefz/BUFF_SIZE)+1
            # 将帧大小发送到远程主机
            c_socket.sendto(str(sizefz).encode('utf-8'),remote)
            # set reciving timeout
            c_socket.settimeout(10)
            # 接收确认
            returneds,addr=c_socket.recvfrom(BUFF_SIZE)
            # comfirm
            if returneds.decode('utf-8')!=str(sizefz):release()
            # 开始传输视频数据，注意这边我设定每隔 8 个UDP 包进行一次确认，具体原因见README
            for _ in range(packnum):
                c_socket.sendto(framez[_*BUFF_SIZE:(_+1)*BUFF_SIZE],remote)
                # comfirm every 8 pack
                if not _%8:
                    try:
                        returned,addr=c_socket.recvfrom(BUFF_SIZE)
                        if returned.decode('utf-8')!=str(_):_=int(returned.decode('utf-8'))
                    except Exception:
                        print('connection lost')
                        release()
                else:
                    pass
    window.destroy()
    cwindow = tk.Tk()
    cwindow.title('video stream client')
    cwindow.geometry('300x200')
    tk.Label(cwindow, text='remote host:', font=('black', 14)).pack(side='top')
    entrytext = tk.Entry(cwindow, width=25, font=('black', 14))
    entrytext.pack(side='top')
    tk.Button(cwindow, text='stop camera', command=exit).pack(side='bottom')
    tk.Button(cwindow, text='start camera', command=as_client).pack(side='bottom')
# 接收端
def as_server():
    # 建立 UDP 套接字，并与本机 IP 地址绑定
    s_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    s_socket.bind(('',PORT))
    # set reciving timeout
    s_socket.settimeout(60)
    while True:
        # 接收帧大小并回复以确认
        sizezfs, clientaddr = s_socket.recvfrom(BUFF_SIZE)
        sizefz=int(sizezfs.decode('utf-8'))
        s_socket.sendto(sizezfs,clientaddr)
        packnum=int(sizefz/BUFF_SIZE)+1
        # 开始接收视频数据
        bframe=b''
        for _ in range(packnum):
            try:
                data, addr = s_socket.recvfrom(BUFF_SIZE)
                bframe+=data
                if not _%8:
                    s_socket.sendto(str(_).encode(),clientaddr)
            except Exception:
                print('connection lost')
                # release all
                cv2.destroyAllWindows()
                s_socket.close()
        # 解压缩并转换帧格式
        frame=pickle.loads(decompress(bframe))
        # Display the resulting frame
        cv2.imshow('Remote Video', frame)
        # press these keys to quit
        if cv2.waitKey(1) & 0xFF == ord(' '):
            break
    # release all
    cv2.destroyAllWindows()
    s_socket.close()
def click_s():
    window.destroy()
    swindow = tk.Tk()
    swindow.title('video stream server')
    swindow.geometry('300x200')
    tk.Button(swindow, text='start server', font=('black', 14), command=as_server).pack(side='bottom')
window = tk.Tk()
window.title('video stream')
window.geometry('300x200')
tk.Button(window, text='Client', font=('black', 14), command=click_c).pack(side='top')
tk.Button(window, text='Server', font=('black', 14), command=click_s).pack(side='top')
window.mainloop()
