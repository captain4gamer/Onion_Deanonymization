MESSAGE_LENGTH_BYTES = 5


def create_message(message):
    """
    :param message: a message
    :return: wraps the message in the protocol format and returns it
    """
    return str(len(message)).zfill(MESSAGE_LENGTH_BYTES) + message


def receive_message(sock):
    """
    :param sock: socket connection
    :return: returns a message
    """
    message_length = sock.recv(MESSAGE_LENGTH_BYTES).decode()
    print("message_length:", message_length)
    if len(message_length) != MESSAGE_LENGTH_BYTES or not str.isdigit(message_length):
        return False, ""

    message = sock.recv(int(message_length)).decode()
    print("message:", message)
    if len(message) != int(message_length):
        return False, ""
    return True, message
