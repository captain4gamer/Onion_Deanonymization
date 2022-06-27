HACKER_SERVER_PORT = 50001
MESSAGE_LENGTH_BYTES = 5
PORT_LENGTH_BYTES = 1
CONNECTION_COUNTER_LENGTH = 10
FIELD_LENGTH_BYTES = 2

# msg_type 0:
# fake relay tells that he is the last in the route

# msg_type 1:
# relay sends connection information

# msg_type 2:
# relay sends a message

# msg_type 3:
# asks if a relay is a fake relay


# TODO: comment
def create_message(msg_type, args):
    # args: id
    if msg_type == 0:
        return "0" + str(len(args[0])).zfill(FIELD_LENGTH_BYTES) + args[0]

    # args: port/id, port/id
    if msg_type == 1:
        message = "1"

        if type(args[0]) == str:
            message += str(len(args[0])).zfill(FIELD_LENGTH_BYTES) + args[0]
        else:
            message += str(len(str(args[0]))).zfill(FIELD_LENGTH_BYTES) + str(args[0])
        if type(args[1]) == str:
            message += str(len(args[1])).zfill(FIELD_LENGTH_BYTES) + args[1]
        else:
            message += str(len(str(args[1]))).zfill(FIELD_LENGTH_BYTES) + str(args[1])
        return message

    # args: id, message
    if msg_type == 2:
        return "2" + str(len(args[0])).zfill(FIELD_LENGTH_BYTES) + args[0] + str(len(args[1])).zfill(MESSAGE_LENGTH_BYTES) + args[1]

    # args: is_from_relay
    # if is_from_relay == True -> args[1]: port, args[2]: port
    # if is_from_relay == False -> args[1] is the answer from the server(0 or 1)
    if msg_type == 3:
        if args[0]:
            return "3" + str(len(str(args[1]))).zfill(FIELD_LENGTH_BYTES) + str(args[1]) + str(len(str(args[2]))).zfill(FIELD_LENGTH_BYTES) + str(args[2])
        else:
            return "3" + str(args[1])

# TODO: comment
def get_msg_type_and_data(data):
    if len(data) < 0:
        return False, "", ""

    msg_type = data[0]
    if not str.isdigit(msg_type):
        return False, "", ""

    return True, int(msg_type), data[1:]


# TODO: comment
def process_message(msg_type, data, from_relay):
    if msg_type == 0:
        if len(data) < FIELD_LENGTH_BYTES:
            return False, []

        id_length = data[:FIELD_LENGTH_BYTES]
        if not str.isdigit(id_length):
            return False, []

        if len(data[FIELD_LENGTH_BYTES:]) < int(id_length):
            return False, []

        # return id
        print("the whole id:", data)
        return True, [data[FIELD_LENGTH_BYTES:]]

    elif msg_type == 1:
        if len(data) < FIELD_LENGTH_BYTES:
            return False, []

        field1_length = data[:FIELD_LENGTH_BYTES]
        data = data[FIELD_LENGTH_BYTES:]

        if not str.isdigit(field1_length):
            return False, []
        field1_length = int(field1_length)

        if len(data) < field1_length:
            return False, []

        field1 = data[:field1_length]
        data = data[field1_length:]

        if len(field1) < 0:
            return False, []

        if field1[0] == "i":
            if field1[:2] != "id" or not str.isdigit(field1[2:]):
                return False, []
        else:
            if not str.isdigit(field1):
                return False, []
            else:
                field1 = int(field1)

        if len(data) < FIELD_LENGTH_BYTES:
            return False, []

        field2_length = data[:FIELD_LENGTH_BYTES]
        data = data[FIELD_LENGTH_BYTES:]

        if not str.isdigit(field2_length):
            return False, []
        field2_length = int(field2_length)

        if len(data) < field2_length:
            return False, []

        field2 = data[:field2_length]
        data = data[field2_length:]

        if len(field2) < 0:
            return False, []

        if field2[0] == "i":
            if field2[:2] != "id" or not str.isdigit(field2[2:]):
                print("err1")
                return False, []
        else:
            if not str.isdigit(field2):
                return False, []
            else:
                field2 = int(field2)

        return True, [field1, field2]

    elif msg_type == 2:
        if len(data) < FIELD_LENGTH_BYTES:
            return False, []

        connection_id_length = data[:FIELD_LENGTH_BYTES]
        data = data[FIELD_LENGTH_BYTES:]

        if not str.isdigit(connection_id_length):
            return False, []
        connection_id_length = int(connection_id_length)

        if len(data) < connection_id_length:
            return False, []

        connection_id = data[:connection_id_length]
        data = data[connection_id_length:]

        if not is_valid_id(connection_id):
            return False, []

        if len(data) < MESSAGE_LENGTH_BYTES:
            return False, []

        msg_length = data[:MESSAGE_LENGTH_BYTES]
        if not str.isdigit(msg_length):
            return False, []

        if len(data[MESSAGE_LENGTH_BYTES:]) < int(msg_length):
            return False, []

        return True, [connection_id, data[FIELD_LENGTH_BYTES:]]

    elif msg_type == 3:
        if from_relay == 1:
            if len(data) < FIELD_LENGTH_BYTES:
                return False, []

            port1_length = data[:FIELD_LENGTH_BYTES]
            data = data[FIELD_LENGTH_BYTES:]

            if not str.isdigit(port1_length):
                return False, []

            port1_length = int(port1_length)
            if len(data) < port1_length:
                return False, []

            port1 = data[:port1_length]
            data = data[port1_length:]
            if not str.isdigit(port1):
                return False, []

            port1 = int(port1)

            if len(data) < FIELD_LENGTH_BYTES:
                return False, []

            port2_length = data[:FIELD_LENGTH_BYTES]
            data = data[FIELD_LENGTH_BYTES:]

            if not str.isdigit(port2_length):
                return False, []

            port2_length = int(port2_length)
            if len(data) < port2_length:
                return False, []

            port2 = data[:port2_length]
            data = data[port2_length:]
            if not str.isdigit(port2):
                return False, []

            port2 = int(port2)

            return True, [port1, port2]
        else:
            if len(data) < 1:
                return False, []

            answer = data[0]
            if not str.isdigit(answer) or (answer != "0" and answer != "1"):
                return False, []

            return True, [int(answer)]


# TODO: comment
def create_connection_id(port, connection_counter):
    return "id" + str(connection_counter).zfill(CONNECTION_COUNTER_LENGTH) + str(port)


# TODO: comment
def is_valid_id(con_id):
    if type(con_id) != str:
        return False

    if len(con_id) < 2 + CONNECTION_COUNTER_LENGTH + 1:
        return False

    if con_id[:2] != "id":
        return False

    if not str.isdigit(con_id[2:]) and int(con_id[2:]) <= 0:
        return False

    if int(con_id[2 + CONNECTION_COUNTER_LENGTH:]) <= 0:
        return False

    return True
