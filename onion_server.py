import socket
import select
import onion_protocol
import random
import main_protocol


def process_data(data, msg_type):
    """
    :param data: packet to be processed
    :param msg_type: the type of the message
    :return: return some data based on the msg_type
    this method supposed to processes packets that come
    """

    # if the message is from a client
    if msg_type == 0:
        # returns the route to the client
        if len(available_ports) < 3:
            print("not enough available ports")
            return False, []

        # chooses 3 random ports
        chosen_connections = random.sample(available_ports, 3)
        chosen_ports = [chosen_connections[0][1], chosen_connections[1][1], chosen_connections[2][1]]
        return True, chosen_ports

    # if the message is from a relay
    elif msg_type == 1:
        # processes and returns a port
        if len(data) < onion_protocol.PORT_LENGTH_BYTES:
            return False, -1
        if not str.isdigit(data[:onion_protocol.PORT_LENGTH_BYTES]):
            return False, -1

        port_length = data[:onion_protocol.PORT_LENGTH_BYTES]
        port = data[onion_protocol.PORT_LENGTH_BYTES:]
        if len(port) < int(port_length) or not str.isdigit(port):
            return False, -1

        return True, int(port)


print("Setting up server...")
server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server_socket.bind(("0.0.0.0", onion_protocol.ONION_SERVER_PORT))
server_socket.listen()
print("Listening for clients...")


client_sockets = []
messages_to_send = []
# available relays to create a route for the clients
available_ports = []


while True:
    rlist, wlist, xlist = select.select([server_socket] + client_sockets, client_sockets, [])
    for current_socket in rlist:
        if current_socket is server_socket:
            connection, client_address = current_socket.accept()
            print("New client joined!", client_address)
            client_sockets.append(connection)
        else:
            print("current socket:", current_socket.getpeername())

            is_valid, msg = main_protocol.receive_message(current_socket)
            if not is_valid:
                print("Connection closed")
                # if it's a relay it will remove it from the availability list
                for con in available_ports:
                    if current_socket == con[0]:
                        available_ports.remove((con[0], con[1]))
                        break
                client_sockets.remove(current_socket)
                current_socket.close()
            else:
                is_valid_msg_type, msg_type, data = onion_protocol.split_type_data(msg)

                if not is_valid_msg_type or (msg_type != 0 and msg_type != 1):
                    print("Connection closed")
                    # if it's a relay it will remove it from the availability list
                    for con in available_ports:
                        if current_socket == con[0]:
                            available_ports.remove((con[0], con[1]))
                            break
                    client_sockets.remove(current_socket)
                    current_socket.close()
                else:
                    is_valid, processed_data = process_data(data, msg_type)
                    if not is_valid:
                        print("Connection closed")
                        # if it's a relay it will remove it from the availability list
                        for con in available_ports:
                            if current_socket == con[0]:
                                available_ports.remove((con[0], con[1]))
                                break
                        client_sockets.remove(current_socket)
                        current_socket.close()

                    if msg_type == 0:
                        msg = onion_protocol.create_message(0, [processed_data])
                        messages_to_send.append((current_socket, main_protocol.create_message(msg).encode()))
                    if msg_type == 1:
                        available_ports.append((current_socket, processed_data))

    for message in messages_to_send:
        current_socket, data = message
        if current_socket in wlist:
            print("data-sent:", data)
            current_socket.send(data)
            messages_to_send.remove(message)
