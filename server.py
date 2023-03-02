import threading
import socket
import time

host = '0.0.0.0'
port = 56789

server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server.bind((host, port))
server.listen()

clients = []
nicknames = []
running = True

def broadcast(message):
    for client in clients:
        client.send(message)

def handle(client):
    global running
    while True:
        try:
            msg = message = client.recv(1024)

            ##### General Commands #####

            # command to get no. of users
            if msg.decode('ascii').startswith('USERS'):
                client.send(f'Connected users: {str(len(clients))}'.encode('ascii'))
            # command to get list of commands
            elif msg.decode('ascii').startswith('HELP'):
                if nicknames[clients.index(client)] == 'admin':
                    client.send('Commands: KICK, BAN, UNBAN, LISTBAN, USERS, NAMES, HELP, LEAVE, CLOSE'.encode('ascii'))
                else:
                    client.send('Commands: USERS, HELP, LEAVE'.encode('ascii'))
            # command to leave the chat
            elif msg.decode('ascii').startswith('LEAVE'):
                name = msg.decode('ascii')[6:]
                index = nicknames.index(name)
                leave_chat(client, index)
                broadcast(f'{name} left the chat!'.encode('ascii'))
                break

            ##### Admin Commands #####

            # command to start the server
            elif msg.decode('ascii').startswith('START'):
                if nicknames[clients.index(client)] == 'admin':
                    running = True
                    client.send('Server started!'.encode('ascii'))
                else:
                    client.send('Command was refused!'.encode('ascii'))
            # command to get names of all users
            elif msg.decode('ascii').startswith('NAMES'):
                if nicknames[clients.index(client)] == 'admin':
                    client.send(f'Connected users: {", ".join(nicknames)}'.encode('ascii'))
                else:
                    client.send('Command was refused!'.encode('ascii'))
            # command to send message to client by admin if he is banned
            elif msg.decode('ascii').startswith('ISBAN'):
                if nicknames[clients.index(client)] == 'admin':
                    name = msg.decode('ascii')[6:]
                    if is_ban(name):
                        client.send(f'{name} is banned!'.encode('ascii'))
                    else:
                        client.send(f'{name} is not banned!'.encode('ascii'))
                else:
                    client.send('Command was refused!'.encode('ascii'))
            # command to kick a user
            elif msg.decode('ascii').startswith('KICK'):
                if nicknames[clients.index(client)] == 'admin':
                    name_to_kick = msg.decode('ascii')[5:]
                    kick_user(name_to_kick)
                else:
                    client.send('Command was refused!'.encode('ascii'))
            # command to ban a user
            elif msg.decode('ascii').startswith('BAN'):
                if nicknames[clients.index(client)] == 'admin':
                    name_to_ban = msg.decode('ascii')[4:]
                    kick_user(name_to_ban)
                    with open('bans.txt', 'r') as f:
                        bans = f.readlines()
                        if is_ban(name_to_ban):
                            client.send(f'{name_to_ban} is already banned!'.encode('ascii'))
                        else:
                            with open('bans.txt', 'a') as f:
                                f.write(f'{name_to_ban}\n')
                            client.send(f'{name_to_ban} has been banned from the server'.encode('ascii'))
                else:
                    client.send('Command was refused!'.encode('ascii'))
            # command to get list of banned users
            elif msg.decode('ascii').startswith('LISTBAN'):
                if nicknames[clients.index(client)] == 'admin':
                    with open('bans.txt', 'r') as f:
                        bans = f.readlines()
                        if len(bans) != 0:
                            client.send(('Banned users: \n\n'+"".join(bans)).encode('ascii'))
                        else:
                            client.send(f'No one is banned currently!!!'.encode('ascii'))
            # command to unban a user
            elif msg.decode('ascii').startswith('UNBAN'):
                if nicknames[clients.index(client)] == 'admin':
                    name_to_unban = msg.decode('ascii')[6:]
                    with open('bans.txt', 'r') as f:
                        bans = f.readlines()
                        if len(bans) != 0:
                            if name_to_unban == '*':
                                with open('bans.txt', 'w') as f:
                                    f.write('')
                                print(f'Banned List was reset!')
                                client.send(f'Banned List is now empty!'.encode('ascii'))
                            elif is_ban(name_to_unban):
                                with open('bans.txt', 'w') as f:
                                    for ban in bans:
                                        if ban.strip('\n') != name_to_unban:
                                            f.write(ban)
                                print(f'{name_to_unban} was unbanned!')
                                client.send(f'{name_to_unban} unbanned successfully!'.encode('ascii'))
                            else:
                                client.send(f'{name_to_unban} is not banned!'.encode('ascii'))
                        else:
                            client.send('No one is banned currently')
                else:
                    client.send('Command was refused!'.encode('ascii'))

            # command to close the server
            elif msg.decode('ascii').startswith('CLOSE'):
                if nicknames[clients.index(client)] == 'admin':
                    running = False
                    client.send('Server closed!'.encode('ascii'))
                    broadcast('Server is closing!'.encode('ascii'))
                    time.sleep(5)
                    for client in clients:
                        client.close()
                    server.close()
                    print('Server closed!')
                    break
                else:
                    client.send('Command was refused!'.encode('ascii'))
            else:
                broadcast(message)
        except:
            index = clients.index(client)
            clients.remove(client)
            client.close()
            nickname = nicknames[index]
            broadcast(f'{nickname} left the chat!'.encode('ascii'))
            nicknames.remove(nickname)
            break

def receive():
    global running
    while True:
        client, address = server.accept()
        print(f"Connected with {str(address)}")
        client.send('NICK'.encode('ascii'))
        nickname = client.recv(1024).decode('ascii')

        if nickname == 'admin':
            client.send('PASS'.encode('ascii'))
            password = client.recv(1024).decode('ascii')

            if password != 'adminpass':
                client.send('REFUSE'.encode('ascii'))
                client.close()
                continue

        if running:
            # check if client is banned
            # send message to client if banned and close connection
            if is_ban(nickname):
                client.send('ISBAN'.encode('ascii'))
                client.close()
                continue

            nicknames.append(nickname)
            clients.append(client)

            print(f"Nickname of the client is {nickname}!")
            broadcast(f"{nickname} joined the chat!".encode('ascii'))
            client.send('Connected to the server!'.encode('ascii'))

            thread = threading.Thread(target=handle, args=(client,))
            thread.start()
        else:
            if nickname == 'admin':
                client.send(f'Do you want to start the server? (Y/N)'.encode('ascii'))
                answer = client.recv(1024).decode('ascii')
                if answer.startswith('Y') or answer.startswith('y'):
                    running = True
                    nicknames.append(nickname)
                    clients.append(client)

                    print(f"Nickname of the client is {nickname}!")
                    broadcast(f"{nickname} joined the chat!".encode('ascii'))
                    client.send('Connected to the server!'.encode('ascii'))

                    thread = threading.Thread(target=handle, args=(client,))
                    thread.start()
                else:
                    client.send('REFUSE'.encode('ascii'))
                    client.close()
                    continue
            else:
                client.send(f'Server is closed! Please contact Admin'.encode('ascii'))
                client.send('REFUSE'.encode('ascii'))
                client.close()
                continue

def kick_user(name):
    if name in nicknames:
        name_index = nicknames.index(name)
        client_to_kick = clients[name_index]
        clients.remove(client_to_kick)
        client_to_kick.send('You were kicked by the admin!'.encode('ascii'))
        client_to_kick.close()
        nicknames.remove(name)
        broadcast(f'{name} was kicked by the admin!'.encode('ascii'))
    else:
        print(name + " is not connected to the server!")

def is_ban(name):
    with open('bans.txt', 'r') as f:
        bans = f.readlines()
    for ban in bans:
        if name == ban.rstrip('\n'):
            return True
    return False

def leave_chat(client, index):
    clients.remove(clients[index])
    nicknames.remove(nicknames[index])
    client.close()

def close_server():
    global running
    running = False
    for client in clients:
        client.send('Server is closing!'.encode('ascii'))
        client.close()
    server.close()
    print("Server is closed!")

print("Server is listening...")
receive()
