import socket
import threading

nickname = input("Choose your nickname: ")
if nickname == 'admin':
    password = input("Enter the password for admin: ")

host = '20.251.40.123'
port = 56789

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
            # command to get no. of users
            if message[len(nickname)+2:].startswith('/users'):
                client.send('USERS'.encode('ascii'))
            # command to leave the chat
            elif message[len(nickname)+2:].startswith('/leave'):
                client.send(f'LEAVE {nickname}'.encode('ascii'))
                client.close()
                break
            # command to get list of available commands
            elif message[len(nickname)+2:].startswith('/help'):
                client.send('HELP'.encode('ascii'))
            elif nickname == 'admin':
                # command to get name of all users
                if message[len(nickname)+2:].startswith('/names'):
                    client.send('NAMES'.encode('ascii'))
                # command to get list of banned users
                elif message[len(nickname)+2:].startswith('/listban'):
                    client.send('LISTBAN'.encode('ascii'))
                # command to kick a user
                elif message[len(nickname)+2:].startswith('/kick '):
                    client.send(f'KICK {message[len(nickname)+8:]}'.encode('ascii'))
                # command to ban a user
                elif message[len(nickname)+2:].startswith('/ban '):
                    client.send(f'BAN {message[len(nickname)+7:]}'.encode('ascii'))
                # command to unban a user
                elif message[len(nickname)+2:].startswith('/unban '):
                    client.send(f'UNBAN {message[len(nickname)+9:]}'.encode('ascii'))
                # command to close the server
                elif message[len(nickname)+2:].startswith('/close'):
                    client.send('CLOSE'.encode('ascii'))
                    break
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
