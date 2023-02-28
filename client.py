import socket
import threading

nickname = input("Choose your nickname: ")
if nickname == 'admin':
    password = input("Enter the password for admin: ")

host = '127.0.0.1'
port = 55555

client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
client.connect((host, port))

stop_thread = False

def receive():
    while True:
        global stop_thread
        if stop_thread:
            break
        try:
            message = client.recv(1024).decode('ascii')
            if message == 'NICK':
                client.send(nickname.encode('ascii'))
                next_message = client.recv(1024).decode('ascii')
                if next_message == 'PASS':
                    client.send(password.encode('ascii'))
                    if client.recv(1024).decode('ascii') == 'REFUSE':
                        print("Connection was refused! Incorrect password!")
                        stop_thread = True
                elif next_message == 'BAN':
                    print("Connection was refused! You are banned! Press Enter to exit...")
                    client.close()
                    stop_thread = True
            else:
                print(message)
        except:
            print("An error occurred! Press Enter to exit...")
            client.close()
            break

def write():
    while True:
        if stop_thread:
            break
        message = f'{nickname}: {input("")}'
        if message[len(nickname)+2:].startswith('/'):
            if message[len(nickname)+2:].startswith('/leave'):
                client.send(f'LEAVE {nickname}'.encode('ascii'))
                client.close()
                break
            if nickname == 'admin':
                if message[len(nickname)+2:].startswith('/kick'):
                    client.send(f'KICK {message[len(nickname)+8:]}'.encode('ascii'))
                elif message[len(nickname)+2:].startswith('/ban'):
                    client.send(f'BAN {message[len(nickname)+7:]}'.encode('ascii'))
                elif message[len(nickname)+2:].startswith('/unban'):
                    client.send(f'UNBAN {message[len(nickname)+9:]}'.encode('ascii'))
                else:
                    print("Command not found!")
            else:
                print("This command can only be used by admin!")
        else:
            client.send(message.encode('ascii'))


receive_thread = threading.Thread(target=receive)
receive_thread.start()

write_thread = threading.Thread(target=write)
write_thread.start()
