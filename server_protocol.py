SERVER_PORT = 30000
MESSAGE_LENGTH_BYTES = 5


def create_message(message):
    """
    :param message: message
    :return: wraps the message in the protocol format and returns it
    """
    return str(len(message)).zfill(MESSAGE_LENGTH_BYTES) + message


def process_data(data):
    """
    :param data: packet to be processed
    :return: process the data and unwraps it from the protocol format
    """
    if len(data) < MESSAGE_LENGTH_BYTES:
        return False, ""

    message_length = data[:MESSAGE_LENGTH_BYTES]
    if not str.isdigit(message_length) or int(message_length) != len(data[MESSAGE_LENGTH_BYTES:]):
        return False, ""

    return True, data[MESSAGE_LENGTH_BYTES:]


def create_reply(message):
    """
    :param message: message
    :return: creates a relpy and returns it
    """
    return "hello " + message
