import socket
import select
import onion_protocol
import server_protocol
import main_protocol
import encryption_methods
import client_methods


NUMBER_OF_PORTS = 3


def unpack_message(data, keys):
    """
    :param data: data from relay
    :param keys: keys to decrypt the data
    :return: decrypts the data and returns it
    """
    if keys == []:
        return True, data
    unencrypted_data = encryption_methods.encrypt(data, keys[0])

    for i in range(len(keys) - 1):
        unencrypted_data = encryption_methods.encrypt(unencrypted_data, keys[i + 1])

    return True, unencrypted_data


def pack_message(data, keys):
    """
    :param data: data to send
    :param keys: keys to encrypt the data
    :return: returns encrypted data
    """
    encrypted_message = data
    for i in range(len(keys)):
        encrypted_message = encryption_methods.encrypt(encrypted_message, keys[i])
    return encrypted_message


def process_data(data, msg_type, args):
    """
    :param data: packet to be processed
    :param msg_type: the type of the message
    :param args: args
    :return: returns some data based on the msg_type and args
    this method supposed to processes packets that come to the client
    """

    # extracts 3 ports from the packet
    if msg_type == 0:
        ports = []

        for i in range(NUMBER_OF_PORTS):
            if len(data) < onion_protocol.PORT_LENGTH_BYTES:
                return False, []

            port_length = data[:onion_protocol.PORT_LENGTH_BYTES]
            if not str.isdigit(port_length):
                return False, []

            data = data[onion_protocol.PORT_LENGTH_BYTES:]
            if len(data) < int(port_length):
                return False, []

            if not str.isdigit(data[:int(port_length)]):
                return False, []

            ports.append(int(data[:int(port_length)]))
            data = data[int(port_length):]

        return True, ports

    # returns part of a key from a key exchange
    elif msg_type == 2:
        # arguments: level

        # level 0
        if args[0] == 0:

            if len(data) < onion_protocol.MESSAGE_LENGTH_BYTES:
                return False, ""

            message_length = data[:onion_protocol.MESSAGE_LENGTH_BYTES]
            if not str.isdigit(message_length):
                return False, ""

            message = data[onion_protocol.MESSAGE_LENGTH_BYTES:]
            if len(message) < int(message_length):
                return False, ""

            if not str.isdigit(message):
                return False, ""

            return True, int(message)

        # level 1 and 2
        # extracts 0/1 from the packet
        elif args[0] == 1 or args[0] == 2:
            if len(data) < onion_protocol.MESSAGE_LENGTH_BYTES:
                return False, ""

            message_length = data[:onion_protocol.MESSAGE_LENGTH_BYTES]
            if not str.isdigit(message_length):
                return False, ""

            message = data[onion_protocol.MESSAGE_LENGTH_BYTES:]
            if len(message) != 1:
                return False, ""

            if not str.isdigit(message):
                return False, ""

            return True, int(message)

        # level 3
        # extracts a message from the packet
        elif args[0] == 3:
            if len(data) < onion_protocol.MESSAGE_LENGTH_BYTES:
                return False, ""

            message_length = data[:onion_protocol.MESSAGE_LENGTH_BYTES]
            if not str.isdigit(message_length):
                return False, ""

            message = data[onion_protocol.MESSAGE_LENGTH_BYTES:]
            if len(message) < int(message_length):
                return False, ""

            return True, message

    return False, ""


def main():
    # generates a lit of messages to send to the server it wants to communicate with
    # through the tor network
    list_of_messages_to_server = client_methods.generate_messages_for_server()
    # index of the message the client will send to the server from the generated messages
    message_to_server_index = 0

    # asking onion server for a route
    onion_socket = socket.socket()
    onion_socket.connect(("127.0.0.1", onion_protocol.ONION_SERVER_PORT))
    msg = onion_protocol.create_message(0, [])
    onion_socket.send(main_protocol.create_message(msg).encode())

    is_valid, msg = main_protocol.receive_message(onion_socket)
    if not is_valid:
        onion_socket.close()
        return

    is_valid, msg_type, data = onion_protocol.split_type_data(msg)

    if not is_valid or msg_type != 0:
        onion_socket.close()
        return

    is_valid, ports = process_data(data, msg_type, [])
    if not is_valid:
        onion_socket.close()
        return

    ports.append(server_protocol.SERVER_PORT)

    # creating a connection with the first relay
    relay_socket = socket.socket()
    relay_socket.connect(("127.0.0.1", ports[0]))

    keys = []
    # the stage of communication which the client is currently in with a relay
    # the level indicates what message/msg type will the client will send to the relay
    level = 0
    # number of relays connected to
    relay_number = 1

    # variables to create a key for encryption
    key_a = encryption_methods.get_number()
    P, G = encryption_methods.get_P_and_G()
    key_aG = encryption_methods.create_key(G, key_a, P)
    key_abG = -1

    msg = onion_protocol.create_message(2, [True, 0, P, G])
    messages_to_send = [
        (relay_socket, main_protocol.create_message(msg).encode())
    ]

    while True:
        rlist, wlist, xlist = select.select([relay_socket], [relay_socket], [])

        for message in messages_to_send:
            current_socket, data = message
            if current_socket in wlist:
                print("data-sent:",data)
                current_socket.send(data)
                messages_to_send.remove(message)

        for current_socket in rlist:
            is_valid, msg = main_protocol.receive_message(current_socket)
            if not is_valid:
                print("Connection closed")
                current_socket.close()
                return False

            # decrypting the message
            is_valid, msg = unpack_message(msg, keys)
            if not is_valid:
                print("Connection closed")
                current_socket.close()
                return

            # the client checks if it's already connected to a server
            if relay_number <= 3:
                # in case the client is not connected to a server

                is_valid_msg_type, msg_type, data = onion_protocol.split_type_data(msg)
                if not is_valid_msg_type or msg_type != 2:
                    print("Connection closed")
                    current_socket.close()
                    return

                is_valid, processed_data = process_data(data, msg_type, [level])

                unencrypted_msg = ""
                if not is_valid:
                    print("Connection closed")
                    current_socket.close()
                    return

                # first part of the key exchange process
                if level == 0:
                    key_bG = processed_data
                    key_abG = encryption_methods.create_key(key_bG, key_a, P)
                    unencrypted_msg = onion_protocol.create_message(2, [True, 1, key_aG])
                    level += 1

                # the final part of the key exchange
                elif level == 1:
                    if processed_data != 1:
                        print("Connection closed")
                        current_socket.close()
                        return

                    # the key is added to the list
                    keys.append(key_abG)
                    unencrypted_msg = onion_protocol.create_message(2, [True, 2, ports[relay_number]])
                    level += 1

                # checks if the relay could connect to the next relay
                elif level == 2:
                    if processed_data != 1:
                        print("Connection closed")
                        current_socket.close()
                        return
                    relay_number += 1

                    # resetting variables
                    level = 0
                    key_a = encryption_methods.get_number()
                    P, G = encryption_methods.get_P_and_G()
                    key_aG = encryption_methods.create_key(G, key_a, P)
                    key_abG = -1

                    # checks if the next entity that the client will communicate with is
                    # a relay or a server
                    if relay_number < 4:
                        unencrypted_msg = onion_protocol.create_message(2, [True, 0, P, G])
                    else:
                        unencrypted_msg = server_protocol.create_message(list_of_messages_to_server[0])

                # encrypting messages to send
                encrypted_msg = pack_message(unencrypted_msg, keys)
                messages_to_send.append((current_socket, main_protocol.create_message(encrypted_msg).encode()))

            else:
                # in case the client is connected to the server

                is_valid, processed_data2 = server_protocol.process_data(msg)
                if not is_valid:
                    print("Connection closed")
                    current_socket.close()
                    return

                print("server's answer:" + processed_data2)

                message_to_server_index += 1

                # checks if it has sent all of the messages to the server
                if message_to_server_index < len(list_of_messages_to_server):
                    unencrypted_msg = server_protocol.create_message(list_of_messages_to_server[message_to_server_index])
                    encrypted_msg = pack_message(unencrypted_msg, keys)
                    messages_to_send.append((current_socket, main_protocol.create_message(encrypted_msg).encode()))
                else:
                    print("finished")
                    current_socket.close()
                    return


main()
