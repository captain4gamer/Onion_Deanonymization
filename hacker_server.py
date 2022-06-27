import main_protocol
import hacker_server_protocol
import socket
import select
import time


# the max time the hacker server will check if a relay is fake before returning an answer back
TIME_DIFFERENCE_MAX_CONNECT = 4
# the max time between the forwarding of the messages, in which you can state that they are related
TIME_DIFF_RESULTS = 2


def write_into_file(data, name, clear):
    """
    :param data: data to write into a file
    :param name: the name of the file
    :param clear: should the method clear the content of the file before writing in it
    :return: writes a message into a file
    """

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
    """
    :param msg_type: message type
    :param data: data from fake relay to be processed
    :param current_sock: the socket of a fake relay
    :return: processes the data received from the fake relay and converts to simple data
    """

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

    # fake relay sending request to this hacker server to ask if another relay is a fake relay
    if msg_type == 3:
        fake_relays_connect.append((
            d[0], d[1], current_sock, time.mktime(time.localtime())
        ))

        return True, []


def is_port_fake_relay(port):
    """
    :param port: port
    :return: checks if a port is of a fake relay
    """
    for sock in client_sockets:
        if port == sock.getpeername():
            return True
    return False


def connect_fake_relays():
    """
    :return: when a pair of fake relays check eachother if they are a fake relay they send it to
    the hacker which will add to the list "fake_relay_connect"
    this method will check if two fake relays asked this question on each other
    and if they did it will send them a confirmation that the other is a fake relay
    """

    i = 0
    while i < len(fake_relays_connect):
        j = i
        fake_relay1 = fake_relays_connect[i]
        fake_relay2 = None

        # iterating through to find 2 which ask about each other if they are a fake relay
        while j < len(fake_relays_connect):
            fake_relay2 = fake_relays_connect[j]

            # if they are found
            if fake_relay1[0] == fake_relay2[1] and fake_relay1[1] == fake_relay2[0]:
                # hacker server sends them a message that the other relay is a fake relay
                messages_to_send.append((fake_relay1[2], main_protocol.create_message(hacker_server_protocol.create_message(3, [False, 1])).encode()))
                messages_to_send.append((fake_relay2[2], main_protocol.create_message(hacker_server_protocol.create_message(3, [False, 1])).encode()))
                fake_relays_connect.remove(fake_relay1)
                fake_relays_connect.remove(fake_relay2)
                i -= 1
                break

            fake_relay2 = None
            j += 1

        if fake_relay2 is None:
            # if didn't found any, it will check if the entry was sitting for too long in the list
            if time.mktime(time.localtime()) - fake_relay1[3] > TIME_DIFFERENCE_MAX_CONNECT:
                # if it was sitting too long in the list it will delete it
                messages_to_send.append((fake_relay1[2], main_protocol.create_message(hacker_server_protocol.create_message(3, [False, 0])).encode()))
                fake_relays_connect.remove(fake_relay1)
                i -= 1

        i += 1


def process_log():
    """
    :return: processes the log of data
    connects relays and ports and returns a result
    """

    # processed data from the log
    log_in_processing = []
    # the result that will be returned
    results = []

    # the data in "log_in_processing" will be stored as:
    # {"origin":__,"relays":[],"is_there_last": True/False, "messages_sent":[]}
    # this lines will created half empty dictionaries with the origin field filled
    for element in log:
        # checks if msg_type is 1
        if element[0] == 1:
            # checks if the first field is a port
            if not hacker_server_protocol.is_valid_id(element[1]):
                log_in_processing.append(
                    {"origin": element[1],
                     "relays": [element[2]],
                     "is_there_last": False,
                     "messages_sent": []}
                )

    # adds the rest of the relays to log_in_processing
    for i in range(2):
        for element in log:
            # checks if message type is 1
            if element[0] == 1:
                field1 = element[1]
                field2 = element[2]
                for elem in log_in_processing:
                    # checks if the relay and the relay stored in log_in_processing are related
                    if elem["relays"][-1] == field1 and hacker_server_protocol.is_valid_id(field2):
                        elem["relays"].append(field2)

    # updating the "is_there_last" to True for some entries that have relay that is last in the route
    for element in log:
        # checks if message type is 0
        if element[0] == 0:
            field = element[1]
            for elem in log_in_processing:
                if field in elem["relays"]:
                    elem["is_there_last"] = True

    # inserts the messages to "message_sent"
    # it will insert the messages of the closest relay to the server
    for element in log:
        if element[0] == 2:
            field = element[1]
            message = element[2]
            for elem in log_in_processing:
                if field == elem["relays"][-1]:
                    elem["messages_sent"].append((message, element[3]))

    # searching for a fake_relay->relay->fake_relay->server route
    # and adding it to the results
    index1 = 0
    print(log_in_processing)
    while index1 < len(log_in_processing):
        element1 = log_in_processing[index1]

        # checks if the entry has a single relay that is not the last
        if len(element1["relays"]) == 1 and not element1["is_there_last"]:
            index2 = 0

            while index2 < len(log_in_processing):
                element2 = log_in_processing[index2]

                # checks if it's not the same relay
                # checks if the other entry has only one relay and it is the last
                if element1 != element2 and len(element2["relays"]) == 1 and element2["is_there_last"]:
                    found = True
                    for i in range(1, 5):
                        # checks the last 4 messages that the relays have forwarded have the same length
                        # and if they were forwarded in approximately the same time
                        if element1["messages_sent"][-i][0][:3] != element2["messages_sent"][-i][0][:3] or abs(
                                element1["messages_sent"][-i][1] - element2["messages_sent"][-i][1]) > TIME_DIFF_RESULTS:
                            found = False

                    if found:
                        # if they are found, they will be added to the results list
                        results.append({
                            "path": [str(element1["origin"]), element1["relays"][0], "?", element2["relays"][0], "server"],
                            "messages": [m[0][3:] for m in element2["messages_sent"]]
                        })
                        log_in_processing.remove(element1)
                        log_in_processing.remove(element2)
                        index1 -= 1
                        break

                index2 += 1
        index1 += 1

        # adding the rest of the relays and data to the list of results
        for element in log_in_processing:
            # adds only if there is a last relay in a route
            if element["is_there_last"]:
                # if it has 3 fake relays, the origin can be traced and will be added to the results
                if len(element["relays"]) == 3:
                    origin = str(element["origin"])
                else:
                    origin = "?"

                # appending data
                results.append({
                    "path": [origin] + element["relays"] + ["server"],
                    "messages": [m[0][3:] for m in element["messages_sent"]]
                })
        return results


def write_results(results):
    """
    :param results: results of process_log()
    :return: writes the results in a more readable way inside of a file
    """

    # clearing the file
    write_into_file("", "results.txt", True)

    r = ""
    for result in results:
        r += "path:" + "->".join(result["path"]) + "\n"
        r += "messages sent:\n"
        for m in result["messages"]:
            r += m + "\n"
        r += "\n\n"

    write_into_file(r, "results.txt", False)
    print("finished results")

x = 0

print("Setting up server...")
server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server_socket.bind(("0.0.0.0", hacker_server_protocol.HACKER_SERVER_PORT))
server_socket.listen()
print("Listening for clients...")


client_sockets = []
# the data that the fake relays have sent
log = []
messages_to_send = []
# a list in which the request of fake relays in which they ask if a port is of a fake relay, are stored
fake_relays_connect = []


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
        write_results(data_to_write)
        x = 0

    for message in messages_to_send:
        current_socket, data = message
        if current_socket in wlist:
            print("data-sent:", data)
            current_socket.send(data)
            messages_to_send.remove(message)
