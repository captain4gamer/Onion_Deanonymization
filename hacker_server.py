import main_protocol
import hacker_server_protocol
import socket
import select
import time


TIME_DIFFERENCE_MAX_CONNECT = 4
TIME_DIFF_RESULTS = 2


def write_into_file(data, name, clear):
    try:
        if clear:
            with open(name, "w") as file:
                file.write(data)
        else:
            with open(name, "a") as file:
                file.write(data)
        return True
    except:
        return False


def process_data(msg_type, data, current_sock):
    valid, d = hacker_server_protocol.process_message(msg_type, data, 1)
    if not valid:
        return False, []

    if msg_type == 0:
        # <d[0]> is the last layer in a route
        return True, (0, d[0], time.mktime(time.localtime()))

    if msg_type == 1:
        # d[0] connected to d[1]
        return True, (1, d[0], d[1], time.mktime(time.localtime()))

    if msg_type == 2:
        # d[0] has passed the message: d[1]
        return True, (2, d[0], d[1], time.mktime(time.localtime()))

    if msg_type == 3:
        fake_relays_connect.append((
            d[0], d[1], current_sock, time.mktime(time.localtime())
        ))

        return True, []


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
            if time.mktime(time.localtime()) - fake_relay1[3] > TIME_DIFFERENCE_MAX_CONNECT:
                messages_to_send.append((fake_relay1[2], main_protocol.create_message(hacker_server_protocol.create_message(3, [False, 0])).encode()))
                fake_relays_connect.remove(fake_relay1)
                i -= 1

        i += 1
        if i < 0:
            i = 0


def process_log():
    print(log)
    log_in_processing = []
    results = []

    # creating origins and it's connection to a fake relay
    for element in log:
        # checks if it's a connection between two entities
        if element[0] == 1:
            # checks if the first field is a port
            if not hacker_server_protocol.is_valid_id(element[1]):
                log_in_processing.append(
                    {"origin": element[1],
                     "relays": [element[2]],
                     "is_there_last": False,
                     "messages_sent": []}
                )

    # connected rest of the relays
    for i in range(2):
        for element in log:
            if element[0] == 1:
                field1 = element[1]
                field2 = element[2]
                for elem in log_in_processing:
                    if elem["relays"][-1] == field1 and hacker_server_protocol.is_valid_id(field2):
                        elem["relays"].append(field2)

    # check if there is a last relay
    for element in log:
        if element[0] == 0:
            field = element[1]
            for elem in log_in_processing:
                if field in elem["relays"]:
                    elem["is_there_last"] = True

    # add messages related
    for element in log:
        if element[0] == 2:
            field = element[1]
            message = element[2]
            for elem in log_in_processing:
                if field == elem["relays"][-1]:
                    elem["messages_sent"].append((message, element[3]))

    # searching for a <fake relay, relay, fake relay> route
    index1 = 0
    print(log_in_processing)
    while index1 < len(log_in_processing):
        element1 = log_in_processing[index1]

        if len(element1["relays"]) == 1 and not element1["is_there_last"]:
            index2 = 0

            while index2 < len(log_in_processing):
                element2 = log_in_processing[index2]

                if element1 != element2 and len(element2["relays"]) == 1 and element2["is_there_last"]:
                    found = True
                    for i in range(1, 5):
                        if element1["messages_sent"][-i][0][:3] != element2["messages_sent"][-i][0][:3] or abs(
                                element1["messages_sent"][-i][1] - element2["messages_sent"][-i][1]) > TIME_DIFF_RESULTS:
                            found = False

                    if found:
                        results.append({
                            "path": [str(element1["origin"]), element1["relays"][0], "?", element2["relays"][0],
                                     "server"],
                            "messages": [m[0][3:] for m in element2["messages_sent"]]
                        })
                        log_in_processing.remove(element1)
                        log_in_processing.remove(element2)
                        index1 -= 1
                        break

                index2 += 1
        index1 += 1

        # adding the rest
        for element in log_in_processing:
            if element["is_there_last"]:
                if len(element["relays"]) == 3:
                    origin = str(element["origin"])
                else:
                    origin = "?"

                results.append({
                    "path": [origin] + element["relays"] + ["server"],
                    "messages": [m[0][3:] for m in element["messages_sent"]]
                })
        print("finished")
        return results


def write_results(results):
    # clear
    print("write1")
    write_into_file("", "results.txt", True)

    print("write2")
    r = ""
    for result in results:
        r += "path:" + "->".join(result["path"]) + "\n"
        r += "messages sent:\n"
        for m in result["messages"]:
            r += m + "\n"
        r += "\n\n"

    print("write3")
    write_into_file(r, "results.txt", False)


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

                    if dat != []:
                        log.append(dat)

    connect_fake_relays()

    x += 1
    if x == 1000000 and log != []:
        data_to_write = process_log()
        print("now this")
        write_results(data_to_write)
        x = 0

    for message in messages_to_send:
        current_socket, data = message
        if current_socket in wlist:
            print("data-sent:", data)
            current_socket.send(data)
            messages_to_send.remove(message)
