ONION_SERVER_PORT = 50000
RELAY_PORT_RANGE = (30001, 49999)
MESSAGE_LENGTH_BYTES = 5
PORT_LENGTH_BYTES = 1
MESSAGE_TYPE_LENGTH = 1


def create_message(msg_type: int, args: list):
    """
    :param msg_type: message type
    :param args: arguments
    :return: wraps data into a format by the protocol and returns it
    """
    message = str(msg_type)

    if msg_type == 0:
        # arguments: list of ports
        if len(args) != 0:
            # wraps the ports of the onion route
            for port in args[0]:
                message += str(len(str(port))).zfill(PORT_LENGTH_BYTES) + str(port)
        return message
    
    elif msg_type == 1:
        # arguments: port

        # wraps a port
        return message + str(len(str(args[0]))).zfill(PORT_LENGTH_BYTES) + str(args[0])
    
    elif msg_type == 2:
        # arguments: from client, level, args

        # checks if the message is from the client
        if args[0]:
            if args[1] == 0:
                # wraps two numbers
                return message + str(len(str(args[2]))).zfill(MESSAGE_LENGTH_BYTES) + str(args[2]) + str(len(str(args[3]))).zfill(MESSAGE_LENGTH_BYTES) + str(args[3])
            elif args[1] == 1:
                # wraps a number
                return message + str(len(str(args[2]))).zfill(MESSAGE_LENGTH_BYTES) + str(args[2])
            elif args[1] == 2:
                # wraps a port
                return message + str(len(str(args[2]))).zfill(PORT_LENGTH_BYTES) + str(args[2])
        else:
            if args[1] == 0:
                return message + str(len(str(args[2]))).zfill(MESSAGE_LENGTH_BYTES) + str(args[2])
            elif args[1] == 1:
                return message + str(len(str(args[2]))).zfill(MESSAGE_LENGTH_BYTES) + str(args[2])
            elif args[1] == 2:
                return message + str(len(str(args[2]))).zfill(MESSAGE_LENGTH_BYTES) + str(args[2])
        # wraps a message
        if args[1] == 3:
            return message + str(len(args[2])).zfill(MESSAGE_LENGTH_BYTES) + args[2]

        return message

    return "-1"


def split_type_data(data):
    """
    :param data: data that was received from the socket
    :return: splits between the message type and the message and returns it
    """
    if len(data) < MESSAGE_TYPE_LENGTH:
        return False, -1, ""

    if not str.isdigit(data[0]):
        return False, -1, ""

    return True, int(data[0]), data[1:]
