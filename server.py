import threading
import socket

host = '127.0.0.1' # localhost
port = 55555

server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server.bind((host, port))
server.listen()

clients = []
nicknames = []

def broadcast(message):
    for client in clients:
        client.send(message)

def handle(client):
    while True:
        try:
            msg = message = client.recv(1024)

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
                clients.remove(clients[index])
                nicknames.remove(name)
                broadcast(f'{name} left the chat!'.encode('ascii'))
                client.close()
                break
                        
            
            # command to get names of all users
            elif msg.decode('ascii').startswith('NAMES'):
                if nicknames[clients.index(client)] == 'admin':
                    client.send(f'Connected users: {", ".join(nicknames)}'.encode('ascii'))
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
                else:
                    client.send('Command was refused!'.encode('ascii'))
            # command to get list of banned users
            elif msg.decode('ascii').startswith('LISTBAN'):
                if nicknames[clients.index(client)] == 'admin':
                    with open('bans.txt', 'r') as f:
                        bans = f.readlines()
                        client.send(('Banned users: \n\n'+"".join(bans)).encode('ascii'))
            # command to unban a user
            elif msg.decode('ascii').startswith('UNBAN'):
                if nicknames[clients.index(client)] == 'admin':
                    name_to_unban = msg.decode('ascii')[6:]
                    with open('bans.txt', 'r') as f:
                        bans = f.readlines()
                        if is_ban(name_to_unban):
                            with open('bans.txt', 'w') as f:
                                for ban in bans:
                                    if ban.strip('\n') != name_to_unban:
                                        f.write(ban)
                        else:
                            client.send(f'{name_to_unban} is not banned!'.encode('ascii'))

                    print(f'{name_to_unban} was unbanned!')
                else:
                    client.send('Command was refused!'.encode('ascii'))
            # command to kick a user
            elif msg.decode('ascii').startswith('KICK'):
                if nicknames[clients.index(client)] == 'admin':
                    name_to_kick = msg.decode('ascii')[5:]
                    kick_user(name_to_kick)
                else:
                    client.send('Command was refused!'.encode('ascii'))
            # command to close the server
            elif msg.decode('ascii').startswith('CLOSE'):
                if nicknames[clients.index(client)] == 'admin':
                    broadcast('Server is shutting down!'.encode('ascii'))
                    server.close()
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
    while True:
        client, address = server.accept()
        print(f"Connected with {str(address)}")

        client.send('NICK'.encode('ascii'))
        nickname = client.recv(1024).decode('ascii')

        with open('bans.txt', 'r') as f:
            bans = f.readlines()

        if is_ban(nickname):
            client.send('BAN'.encode('ascii'))
            client.close()
            continue

        if nickname == 'admin':
            client.send('PASS'.encode('ascii'))
            password = client.recv(1024).decode('ascii')

            if password != 'adminpass':
                client.send('REFUSE'.encode('ascii'))
                client.close()
                continue

        nicknames.append(nickname)
        clients.append(client)

        print(f"Nickname of the client is {nickname}!")
        broadcast(f"{nickname} joined the chat!".encode('ascii'))
        client.send('Connected to the server!'.encode('ascii'))

        thread = threading.Thread(target=handle, args=(client,))
        thread.start()

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
        print("No user with that name!")

def is_ban(name):
    with open('bans.txt', 'r') as f:
        bans = f.readlines()

    for ban in bans:
        if name == ban.rstrip('\n'):
            return True
    return False


print("Server is listening...")
receive()
