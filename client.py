import config, socket, sys

TCP_PORT = config.PRIMARY_PORT

def TCP_Connection(service, params) -> None:
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    
    try:
        sock.connect((socket.gethostname(), TCP_PORT))

        msg = f'{{ "service" : "{service}", "param" : {params} }}'

        sock.send(bytes(f'{msg}', 'utf-8'))

        print(f'Message {msg} sent to {TCP_PORT}')

        message = sock.recv(1024).decode('utf-8')
        print(f'Message from: {(socket.gethostname(), TCP_PORT)}', f'Message: {message}', sep='\n')
    except Exception as e:
        if str(e) == '[WinError 10054] Foi forçado o cancelamento de uma conexão existente pelo host remoto':
            print('Server closed connection abruptly. Please try again later.')
        else:
            print('Could not connect to server. Please try again later.')
    finally:
        sock.close()

def main(service, params):
    TCP_Connection(service, params)

if __name__ == '__main__':
    args = sys.argv[1:]

    if len(args) < 2:
        print('Incorrect number of arguments passed.', 'Usage:\t\t python client.py SERVICE PARAMS', sep='\n')
        sys.exit(0)
    
    service = args[0]
    params = args[1:]

    services =  ['ALIVE?', 'ADD', 'DO_SOMETHING']

    if not service in services:
        print('Invalid argument. Please provide a valid service [ALIVE?, ADD, DO_SOMETHING].')
        sys.exit(0)

    try:
        params = [int(x) for x in params]
    except:
        print('Invalid argument. Please provide a integer for the numeric values.')
        sys.exit(0)

    main(service, params)