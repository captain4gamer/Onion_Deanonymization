import main_protocol
import hacker_server_protocol
import socket
import select
import time


TIME_DIFFERENCE_MAX = 4


def write_into_file(data, name):
    try:
        with open(name, "w") as file:
            file.write(data)
        return True
    except:
        return False


def process_data(msg_type, data, current_sock):
    valid, d = hacker_server_protocol.process_message(msg_type, data, 1)
    if not valid:
        return False, ""
    if msg_type == 0:
        return True, str(data) + ":is the last"
    if msg_type == 1:
        return True, str(d[0]) + " is connected to " + str(d[1])
    if msg_type == 2:
        return True, str(d[0]) + " sent this message:" + str(d[1])
    if msg_type == 3:
        fake_relays_connect.append((
            d[0], d[1], current_sock, time.mktime(time.localtime())
        ))

        return True, ""

# TODO: comment
def is_port_fake_relay(port):
    for sock in client_sockets:
        if port == sock.getpeername():
            return True
    return False


def connect_fake_relays():
    i = 0
    while i < len(fake_relays_connect):
        j = i
        fake_relay1 = fake_relays_connect[i]
        fake_relay2 = None

        while j < len(fake_relays_connect):
            fake_relay2 = fake_relays_connect[j]
            if fake_relay1[0] == fake_relay2[1] and fake_relay1[1] == fake_relay2[0]:
                messages_to_send.append((fake_relay1[2], main_protocol.create_message(hacker_server_protocol.create_message(3, [False, 1])).encode()))
                messages_to_send.append((fake_relay2[2], main_protocol.create_message(hacker_server_protocol.create_message(3, [False, 1])).encode()))
                fake_relays_connect.remove(fake_relay1)
                fake_relays_connect.remove(fake_relay2)
                i -= 3
                break
            fake_relay2 = None
            j += 1

        if fake_relay2 is None:
            if time.mktime(time.localtime()) - fake_relay1[3] > TIME_DIFFERENCE_MAX:
                messages_to_send.append((fake_relay1[2], main_protocol.create_message(hacker_server_protocol.create_message(3, [False, 0])).encode()))
                fake_relays_connect.remove(fake_relay1)
                i -= 1

        i += 1
        if i < 0:
            i = 0


x = 0

print("Setting up server...")
server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server_socket.bind(("0.0.0.0", hacker_server_protocol.HACKER_SERVER_PORT))
server_socket.listen()
print("Listening for clients...")

client_sockets = []
log = []
messages_to_send = []
fake_relays_connect = []


while True:
    rlist, wlist, xlist = select.select([server_socket] + client_sockets, client_sockets, [])

    for current_socket in rlist:
        if current_socket is server_socket:
            connection, client_address = current_socket.accept()
            print("New client joined!", client_address)
            client_sockets.append(connection)
        else:
            print("current socket:", current_socket.getpeername())
            is_valid, data = main_protocol.receive_message(current_socket)
            if not is_valid:
                print("Connection closed: due to invalid main protocol1")
                client_sockets.remove(current_socket)
                current_socket.close()
            else:
                is_valid, msg_type, data = hacker_server_protocol.get_msg_type_and_data(data)
                if not is_valid:
                    print("Connection closed: due to invalid protocol2")
                    client_sockets.remove(current_socket)
                    current_socket.close()
                else:
                    is_valid_data, dat = process_data(msg_type, data, current_socket)
                    if not is_valid_data:
                        print("Connection closed: due to invalid protocol3")
                        client_sockets.remove(current_socket)
                        current_socket.close()

                    if dat != "":
                        log.append(dat)

    connect_fake_relays()

    # processing the data collected
    # process_data(log)
    x += 1
    if x == 100000:
        write_into_file("\n".join(log), "results.txt")
        x = 0

    for message in messages_to_send:
        current_socket, data = message
        if current_socket in wlist:
            print("data-sent:", data)
            current_socket.send(data)
            messages_to_send.remove(message)

