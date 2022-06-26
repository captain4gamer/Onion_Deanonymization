import socket
import select
import server_protocol
import main_protocol


def main():
    print("Setting up server...")
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.bind(("0.0.0.0", server_protocol.SERVER_PORT))
    server_socket.listen()
    print("Listening for clients...")

    client_sockets = []
    messages_to_send = []

    while True:
        rlist, wlist, xlist = select.select([server_socket] + client_sockets, client_sockets, [])

        for current_socket in rlist:
            if current_socket is server_socket:
                connection, client_address = current_socket.accept()
                print("New client joined!", client_address)
                client_sockets.append(connection)
            else:
                is_valid, data = main_protocol.receive_message(current_socket)

                if not is_valid:
                    print("Connection closed: due to invalid main protocol")
                    client_sockets.remove(current_socket)
                    current_socket.close()
                else:
                    is_valid_data, processed_data = server_protocol.process_data(data)

                    if not is_valid_data:
                        print("Connection closed: due to invalid protocol")
                        client_sockets.remove(current_socket)
                        current_socket.close()

                    reply = server_protocol.create_reply(processed_data)
                    protocol_reply = server_protocol.create_message(reply)
                    messages_to_send.append((current_socket, main_protocol.create_message(protocol_reply).encode()))

        for message in messages_to_send:
            current_socket, data = message
            if current_socket in wlist:
                print("sent-data:",data)
                current_socket.send(data)
                messages_to_send.remove(message)


main()
