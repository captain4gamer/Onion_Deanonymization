import socket
import select
import onion_protocol
import random
import main_protocol
import encryption_methods
import hacker_server_protocol
import server_protocol

TIMEOUT = 20


def process_data(data, msg_type, level):
    """
    :param data: packet to be processed
    :param msg_type: the type of the message
    :param level: level
    :return: return some data based on the msg_type and level
    this method supposed to processes packets that come to the fake relay
    """

    # checks if it should just return the message or process it
    # if level equals to 4 it should just return it
    # which means the fake relays just needs to pass the message
    if level != 4:
        if msg_type == 2:

            # returns two numbers to creates a key for the key exchange
            if level == 0:
                if len(data) < onion_protocol.MESSAGE_LENGTH_BYTES:
                    return False, -1, -1

                message_length = data[:onion_protocol.MESSAGE_LENGTH_BYTES]
                if not str.isdigit(message_length):
                    return False, -1, -1

                data = data[onion_protocol.MESSAGE_LENGTH_BYTES:]
                if len(data) < int(message_length):
                    return False, -1, -1

                # first number
                P = data[:int(message_length)]

                data = data[int(message_length):]
                if len(data) < onion_protocol.MESSAGE_LENGTH_BYTES:
                    return False, -1, -1

                message_length = data[:onion_protocol.MESSAGE_LENGTH_BYTES]
                if not str.isdigit(message_length):
                    return False, -1, -1

                data = data[onion_protocol.MESSAGE_LENGTH_BYTES:]
                if len(data) < int(message_length):
                    return False, -1, -1

                # second number
                G = data[:int(message_length)]

                return True, int(P), int(G)

            # returns a number to create a key
            elif level == 1:
                if len(data) < onion_protocol.MESSAGE_LENGTH_BYTES:
                    return False, -1

                message_length = data[:onion_protocol.MESSAGE_LENGTH_BYTES]
                if not str.isdigit(message_length):
                    return False, -1

                data = data[onion_protocol.MESSAGE_LENGTH_BYTES:]
                if len(data) < int(message_length):
                    return False, -1

                # the number
                key_aG = data[:int(message_length)]

                return True, int(key_aG)

            # returns a port
            elif level == 2:
                if len(data) < onion_protocol.PORT_LENGTH_BYTES:
                    return False, -1

                port_length = data[:onion_protocol.PORT_LENGTH_BYTES]
                if not str.isdigit(port_length):
                    return False, -1

                data = data[onion_protocol.PORT_LENGTH_BYTES:]
                if len(data) < int(port_length):
                    return False, -1

                port = data[:int(port_length)]

                return True, int(port)
    else:
        return True, data


def get_user_values(conn):
    """
    :param conn: connection
    :return: finds the connection in the list "user_values" and returns the values it stores
    """
    for u in user_values:
        if conn == u[0]:
            return u
    return None


def remove_connection(conn):
    """
    :param conn: connection
    :return: removes a connection all the lists and disconnects from it
    """
    found = False

    for c in connect_user_port:
        if c[0] == conn or c[1] == conn:
            c[0].close()
            c[1].close()
            client_sockets.remove(c[0])
            client_sockets.remove(c[1])
            found = True

    if not found:
        client_sockets.remove(conn)
        current_socket.close()

    u = get_user_values(conn)
    if u != None:
        user_values.remove(u)


def send_info(t, args):
    """
    :param t: t for type, indicates the type of the response of the fake relay
    :param args: arguments
    :return: takes information and sends it to the hacker server for deanonymization
    it will send different data or will react accordingly to the variable t
    """

    # args: connection, hacker_socket
    if t == 0:
        # this codes is executed when an entity is connecting to this relay
        # this fake tries to figure if it's a fake relay too
        try:
            _connection = args[0]
            _hacker_socket = args[1]

            _connection.settimeout(TIMEOUT)
            _hacker_socket.settimeout(TIMEOUT)

            # asks the server if it's a fake relay
            _hacker_socket.send(main_protocol.create_message(hacker_server_protocol.create_message(3, [True, _connection.getsockname()[1], _connection.getpeername()[1]])).encode())
            valid, data = main_protocol.receive_message(_hacker_socket)
            if not valid:
                return False

            valid, msg_type, data = hacker_server_protocol.get_msg_type_and_data(data)
            if not valid or msg_type != 3:
                return False

            valid, result = hacker_server_protocol.process_message(3, data, 0)
            if not valid:
                return False

            # if it's a fake relay this fake relay will send his id to the other one
            if result[0] == 1:
                _connection.send(main_protocol.create_message(get_user_values(_connection)[1]["id"]).encode())
            else:
                # if it's not a fkae relay will just information to the hacker server
                connection_port = int(_connection.getpeername()[1])
                conn_id = get_user_values(_connection)[1]["id"]
                m = main_protocol.create_message(hacker_server_protocol.create_message(1, [connection_port, conn_id])).encode()
                _hacker_socket.send(m)

            _connection.settimeout(None)
            _hacker_socket.settimeout(None)

            return True
        except:
            print("except0")
            return False

    # args: hacker_socket, port, temp_socket, current_socket
    if t == 1:
        # this code will be executed when this relay will try to connect to a server or another relay
        try:
            _hacker_socket = args[0]
            _port = args[1]
            _temp_socket = args[2]
            _current_socket = args[3]

            _hacker_socket.settimeout(TIMEOUT)
            _temp_socket.settimeout(TIMEOUT)

            # checks if it tries to connect with a server
            if _port == server_protocol.SERVER_PORT:
                # if it's a server, the relay will send to the hacker_server
                # that it's the last one in the route
                _hacker_socket.send(main_protocol.create_message(hacker_server_protocol.create_message(0, [get_user_values(_current_socket)[1]["id"]])).encode())
            else:
                # if not, it will ask the hacker_server if the relay is a fake relay
                _hacker_socket.send(main_protocol.create_message(hacker_server_protocol.create_message(3, [True, _temp_socket.getsockname()[1], _port])).encode())

                valid, data = main_protocol.receive_message(_hacker_socket)
                if not valid:
                    return False

                valid, msg_type, data = hacker_server_protocol.get_msg_type_and_data(data)
                if not valid or msg_type != 3:
                    return False

                valid, result = hacker_server_protocol.process_message(3, data, 0)
                if not valid:
                    return False

                if result[0]:
                    # if the relay is a fake relay it will receive it's id
                    # and send this id and his id to the hacker_server
                    valid, data = main_protocol.receive_message(_temp_socket)
                    if not valid:
                        return False

                    if not hacker_server_protocol.is_valid_id(data):
                        return False

                    _hacker_socket.send(main_protocol.create_message(hacker_server_protocol.create_message(1, [get_user_values(_current_socket)[1]["id"], data])).encode())
                else:
                    # if not, it will just send his id and the relay port
                    _hacker_socket.send(main_protocol.create_message(hacker_server_protocol.create_message(1, [get_user_values(_current_socket)[1]["id"], _port])).encode())
            _hacker_socket.settimeout(None)
            _temp_socket.settimeout(None)

            return True
        except:
            print("except1")
            return False

    # args: hacker_socket, decrypted_msg, current_socket
    if t == 2:
        # if the fake relay has to pass a message, it will first send it to the hacker_server
        try:
            _hacker_socket = args[0]
            _decrypted_msg = args[1]
            _current_socket = args[2]

            _hacker_socket.send(main_protocol.create_message(hacker_server_protocol.create_message(2, [get_user_values(_current_socket)[1]["id"], _decrypted_msg])).encode())
            return True
        except:
            print("except2")
            return False


MY_PORT = random.randint(onion_protocol.RELAY_PORT_RANGE[0], onion_protocol.RELAY_PORT_RANGE[1])

# connecting to the hacker server
hacker_socket = socket.socket()
hacker_socket.connect(("127.0.0.1", hacker_server_protocol.HACKER_SERVER_PORT))


# connecting to the onion main server
onion_socket = socket.socket()
onion_socket.connect(("127.0.0.1", onion_protocol.ONION_SERVER_PORT))
msg = onion_protocol.create_message(1, [MY_PORT])
onion_socket.send(main_protocol.create_message(msg).encode())


# listening to connections
print("Setting up server...")
server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server_socket.bind(("127.0.0.1", MY_PORT))
server_socket.listen()
print("Listening for clients...")

# connect_user_port stores a list of pairs of ports that are connected through this relay
connect_user_port = []
user_values = []
client_sockets = []
messages_to_send = []


# connections counter for the creation of an id for this fake relay
connection_id = 0

while True:
    rlist, wlist, xlist = select.select([server_socket] + client_sockets, client_sockets, [])
    for current_socket in rlist:
        if current_socket is server_socket:
            connection, client_address = current_socket.accept()
            print("New client joined!", client_address)
            client_sockets.append(connection)

            # stores values for a user to create a key with him later
            # also stores the connection id
            user_values.append(
                (connection,
                     {
                         "level": 0,
                         "key_b": encryption_methods.get_number(),
                         "P": None,
                         "G": None,
                         "key_aG": None,
                         "key_bG": None,
                         "key_abG": None,
                         "id": hacker_server_protocol.create_connection_id(MY_PORT, connection_id)
                     }
                 )
            )
            connection_id += 1

            # sending info to hacker_server
            result = send_info(0, [connection, hacker_socket])
            if not result:
                remove_connection(connection)
        else:
            is_valid, received_msg = main_protocol.receive_message(current_socket)
            if not is_valid:
                remove_connection(current_socket)
            else:

                # checks if the message if going by the route or backwards through the route
                if get_user_values(current_socket) is not None:
                    # if it's going by the route

                    # stores key information and connection id in a variable
                    u_values = get_user_values(current_socket)
                    level = u_values[1]["level"]

                    # creates part of the key for encryption from two numbers
                    if level == 0:
                        is_valid_msg_type, msg_type, dat = onion_protocol.split_type_data(received_msg)

                        if not is_valid_msg_type or msg_type != 2:
                            remove_connection(current_socket)
                        else:
                            is_valid, P, G = process_data(dat, msg_type, 0)

                            if not is_valid:
                                remove_connection(current_socket)
                            else:
                                # stores the two numbers
                                u_values[1]["P"] = P
                                u_values[1]["G"] = G
                                # creates part of the key
                                u_values[1]["key_bG"] = encryption_methods.create_key(G, u_values[1]["key_b"], P)

                                # sending the rest of the information to the other relay to finish the
                                # key creation process
                                msg = onion_protocol.create_message(2, [False, 0, u_values[1]["key_bG"]])
                                messages_to_send.append((current_socket, main_protocol.create_message(msg).encode()))
                                u_values[1]["level"] += 1

                    # receives a number to finish the key creation process
                    elif level == 1:
                        is_valid_msg_type, msg_type, dat = onion_protocol.split_type_data(received_msg)

                        if not is_valid_msg_type or msg_type != 2:
                            remove_connection(current_socket)
                        else:
                            is_valid, key_aG = process_data(dat, msg_type, 1)
                            if not is_valid:
                                remove_connection(current_socket)
                            else:
                                # stores the number
                                u_values[1]["key_aG"] = key_aG
                                # creates a key and stores it
                                u_values[1]["key_abG"] = encryption_methods.create_key(key_aG, u_values[1]["key_b"], u_values[1]["P"])
                                # send a status message to the client that the creation process of the key
                                # was successful
                                msg = onion_protocol.create_message(2, [False, 1, 1])
                                messages_to_send.append((current_socket, main_protocol.create_message(msg).encode()))
                                u_values[1]["level"] += 1

                    # tries to connect with the next relay or with a server
                    elif level == 2:
                        # receives a port from the client to connect to the next relay or server
                        decrypted_msg = encryption_methods.encrypt(received_msg, u_values[1]["key_abG"])
                        is_valid_msg_type, msg_type, dat = onion_protocol.split_type_data(decrypted_msg)

                        if not is_valid_msg_type or msg_type != 2:
                            remove_connection(current_socket)
                        else:
                            is_valid, port = process_data(dat, msg_type, 2)

                            if not is_valid:
                                remove_connection(current_socket)
                            else:
                                # tries to connect with the next relay or with a server
                                try:
                                    temp_socket = socket.socket()
                                    temp_socket.connect(("127.0.0.1", port))

                                    # stores the ports
                                    connect_user_port.append((current_socket, temp_socket))
                                    client_sockets.append(temp_socket)

                                    # sends a message to the client that the connection process was successful
                                    msg = onion_protocol.create_message(2, [False, 2, 1])
                                    encrypted_msg = encryption_methods.encrypt(msg, get_user_values(current_socket)[1]["key_abG"])
                                    messages_to_send.append((current_socket, main_protocol.create_message(encrypted_msg).encode()))

                                    # sends the connection information to the hacker_server
                                    result = send_info(1, [hacker_socket, temp_socket.getpeername()[1], temp_socket, current_socket])
                                    if not result:
                                        remove_connection(current_socket)
                                except:
                                    # in case there was a bug it will send a message that
                                    # he couldn't connect
                                    msg = onion_protocol.create_message(2, [False, 2, 0])
                                    encrypted_msg = encryption_methods.encrypt(msg, u_values[1]["key_abG"])
                                    messages_to_send.append((current_socket, main_protocol.create_message(encrypted_msg).encode()))
                                u_values[1]["level"] += 1

                    # decrypts the message that was received and sends it
                    elif level == 3:
                        decrypted_msg = encryption_methods.encrypt(received_msg, u_values[1]["key_abG"])

                        # sends the decrypted message to the hacker_server
                        result = send_info(2, [hacker_socket, decrypted_msg, current_socket])
                        if not result:
                            remove_connection(current_socket)

                        con = None
                        for connection in connect_user_port:
                            if connection[0] == current_socket:
                                con = connection[1]
                        messages_to_send.append((con, main_protocol.create_message(decrypted_msg).encode()))
                else:
                    # if the message is going backwards through the route
                    # it will pass it
                    conn = None
                    for connection in connect_user_port:
                        if connection[1] == current_socket:
                            conn = connection[0]
                    if conn is None:
                        remove_connection(current_socket)
                    encrypted_msg = encryption_methods.encrypt(received_msg, get_user_values(conn)[1]["key_abG"])
                    messages_to_send.append((conn, main_protocol.create_message(encrypted_msg).encode()))

    for message in messages_to_send:
        current_socket, data = message
        if current_socket in wlist:
            print("data-sent:", data)
            current_socket.send(data)
            messages_to_send.remove(message)
