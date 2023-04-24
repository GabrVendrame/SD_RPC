import socket, errno, sys, config, json, select, threading
from time import sleep, time
from random import randint

PRIMARY_PORT = config.PRIMARY_PORT
SERVER_PORTS = config.SERVER_PORTS

def alive(params : list) -> str:
    return 'Yes'

def add(params : list) -> str:
    try:
        x, y = params[0], params[1]
        
        return f'{x + y}'
    except:
        return 'Cannot perform arithmetic operation on non-numeric values'

def do_something(params : list) -> str:
    time = params[0]

    sleep(time)

    return f'Server slept for {time} seconds'

class TCP_Socket():
    def __init__(self, server_id : int) -> None:
        self.host_alive = True
        self.last_seen = time()

        self.server_id = server_id
        self.is_primary = False

        PORT = SERVER_PORTS[server_id]

        self.port = PORT
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

        self.sock.bind((socket.gethostname(), PORT))
        self.sock.listen(10)

    def set_leader(self) -> None:
        try:
            self.sock.close()

            self.is_primary = True

            # LEADER SOCKET CONFIG
            self.port = PRIMARY_PORT
            self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

            self.sock.bind((socket.gethostname(), PRIMARY_PORT))
            self.sock.listen(10)

            print(self.sock)
        except:
            print('Could not connect to leader port')

            self.host_alive = True
            self.last_seen = time()

            self.server_id = server_id
            self.is_primary = False

            PORT = SERVER_PORTS[server_id]

            self.port = PORT
            self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

            self.sock.bind((socket.gethostname(), PORT))
            self.sock.listen(10)

    def become_primary(self) -> None:
        print(f'TRYING TO BECOME PRIMARY TIMESTAMP: {self.last_seen}\n')
        socks = []

        for port in SERVER_PORTS:
            if port == self.port: continue

            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

            try:
                sock.connect((socket.gethostname(), port))

                sock.send(bytes(f'HOST OFF', 'utf-8'))

                socks.append(sock)
            except Exception as e:
                print(f'Could not connect to server port {port}')

                sock.close()

        for sock in socks:
            data = sock.recv(1024)

            if data:
                msg = json.loads(data.decode('UTF-8'))

                timestamp = float(msg['last_seen'])

                print(f'RECEIVED {timestamp} FROM {sock}')
                
                sock.close()

                if timestamp < self.last_seen:
                    print('LOST')

                    return False
                
        print('WON')

        return True

    def check_alive(self) -> bool:
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

            sock.connect((socket.gethostname(), PRIMARY_PORT))

            sock.send(bytes('{ "service" : "ALIVE?", "param" : {} }', 'UTF-8'))

            data = sock.recv(1024)

            if data:
                print(f'MESSAGE FROM HOST: {data.decode("UTF-8")}')

                sock.close()

                self.last_seen = time()

                return True
        except Exception as e:
            print('HOST OFF')

            sock.close()

        return False
         
    def ping(self) -> None:
        if not self.check_alive():
            self.host_alive = False

            if self.become_primary():
                self.set_leader()
        else:
            self.host_alive = True
        
        if self.is_primary:
            print('EXITING PING FUNCTION')
            return

        next_check = time() + randint(5, 10)
        print(f'Next check in {next_check - time()} seconds')

        while True:
            if time() >= next_check:
                if not self.check_alive():
                    self.host_alive = False

                    if self.become_primary():
                        self.set_leader()
                else:
                    self.host_alive = True
                
                if self.is_primary: break

                next_check = time() + randint(5, 20)
                print(f'Next check in {next_check - time()} seconds')

        print('EXITING PING FUNCTION')

    def secundary_server_stub(self, client_sock, client_addr) -> None:
        try:
            data = client_sock.recv(1024)

            if data:
                msg = data.decode('utf-8')

                if msg == 'HOST OFF':
                    client_sock.send(bytes(f'{{"last_seen" : {self.last_seen}}}', 'UTF-8'))
                else:
                    client_sock.send(bytes('NOOP', 'UTF-8'))
        except Exception as e:
            print('secondary server stub error', e)
        finally:
            client_sock.close()

    def secundary(self):
        threading.Thread(target=self.ping, args=()).start()

        while True:
            if self.is_primary: break
            
            try:
                print("Waiting")
                client_sock, client_addr = self.sock.accept()

                t = threading.Thread(target=self.secundary_server_stub, args=(client_sock, client_addr))

                t.start()
            except Exception as e:
                print('ERROR ON SECUNDARY FUNCTION')
                return

    def dispatcher(self, msg) -> None:
        services = { 'ALIVE?' : alive, 'ADD' : add, 'DO_SOMETHING' : do_something}

        try:
            data = json.loads(msg)

            service, param = data['service'], data['param']

            if service in services:
                return services[service](param)
        except:
            return 'Unexpected error'

    def primary_server_stub(self, client_sock, client_addr) -> None:
        try:
            data = client_sock.recv(1024)

            if data:
                msg = data.decode('utf-8')

                print(f'MESSAGE FROM {client_addr}: {msg}')

                ans = bytes(self.dispatcher(msg), 'utf-8')

                client_sock.send(ans)
        except Exception as e:
            print(f'ERROR ON PRIMARY STUB {e}')
        finally:
            client_sock.close()

    def primary(self) -> None:
        print('PRIMARY SERVER STARTING')
        while True:
            try:
                client_sock, client_addr = self.sock.accept()

                print(f'CONNECTED TO {client_addr}.')

                threading.Thread(target=self.primary_server_stub, args=(client_sock, client_addr)).start()
            except Exception as e:
                print(f'ERROR ON PRIMARY FUNCTION {e}')

    def run(self) -> None:
        while True:
            if self.is_primary:
                self.primary()
            else:
                self.secundary()

def Server(server_id) -> TCP_Socket:
    try:
        return TCP_Socket(server_id)
    except socket.error as e:
        if e.errno == errno.EADDRINUSE:
            print(f'Couldn\'t bind to port {SERVER_PORTS[server_id]}. Terminating process...')
        else:
            print(e)
        
        sys.exit(0)

def main(server_id) -> None:
    server = Server(server_id)
    server.run()

if __name__ == '__main__':
    args = sys.argv[1:]

    if len(args) > 1:
        print('Incorrect number of arguments passed.', 'Usage:\t\t python server.py 1', sep='\n')
        sys.exit(0)
    
    try:
        server_id = int(args[0])

        if server_id > len(SERVER_PORTS) or server_id < 0:
            raise Exception()
    except:
        print(f'Invalid argument. Please provide a integer between 0 and {len(SERVER_PORTS)} for the server ID.')
        sys.exit(0)

    main(server_id)