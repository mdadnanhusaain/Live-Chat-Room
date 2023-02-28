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
            if msg.decode('ascii').startswith('KICK'):
                if nicknames[clients.index(client)] == 'admin':
                    name_to_kick = msg.decode('ascii')[5:]
                    kick_user(name_to_kick)
                else:
                    client.send('Command was refused!'.encode('ascii'))
            elif msg.decode('ascii').startswith('BAN'):
                if nicknames[clients.index(client)] == 'admin':
                    name_to_ban = msg.decode('ascii')[4:]
                    kick_user(name_to_ban)
                    # check if user is already banned or not
                    # if yes, then display a message that he is already banned
                    # if not, then ban him
                    with open('bans.txt', 'r') as f:
                        bans = f.readlines()
                        if is_ban(name_to_ban):
                            client.send(f'{name_to_ban} is already banned!'.encode('ascii'))
                        else:
                            with open('bans.txt', 'a') as f:
                                f.write(f'{name_to_ban}\n')
                else:
                    client.send('Command was refused!'.encode('ascii'))
            elif msg.decode('ascii').startswith('UNBAN'):
                if nicknames[clients.index(client)] == 'admin':
                    name_to_unban = msg.decode('ascii')[6:]
                    with open('bans.txt', 'a+') as f:
                        bans = f.readlines()
                        for ban in bans:
                            if ban.rstrip('\n') != name_to_unban:
                                f.write(ban)
                    print(f'{name_to_unban} was unbanned!')
                else:
                    client.send('Command was refused!'.encode('ascii'))
            elif msg.decode('ascii').startswith('LEAVE'):
                name = msg.decode('ascii')[6:]
                index = nicknames.index(name)
                clients.remove(clients[index])
                nicknames.remove(name)
                broadcast(f'{name} left the chat!'.encode('ascii'))
                client.close()
                break
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

        # check if the user is banned
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
