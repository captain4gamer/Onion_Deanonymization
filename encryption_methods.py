import math
import random

prime_range = (101, 1117)
RANDOM_KEY_RANGE = (1, 100)


def is_prime(x):
    """
    :param x: number
    :return: returns True if it's a prime
    """
    if x < 2:
        return False
    if x == 2:
        return True
    for i in range(2, int(math.sqrt(x))):
        if x % i == 0:
            return False
    return True


def random_prime():
    """
    :return: a random prime
    """
    random_int = random.randint(prime_range[0], prime_range[1])
    while not is_prime(random_int):
        random_int += 1
    return random_int


def get_primitive_primes(prime):
    """
    :param prime: a prime
    :return: returns all of it's primitive roots
    """
    prim_lst = []
    for i in range(2, prime):
        lst = []
        for j in range(1, prime):
            if not int(pow(i, j, prime)) in lst:
                lst.append(int(pow(i, j, prime)))
            else:
                lst = []
                break
        if lst:
            prim_lst.append(i)
    return prim_lst


def random_primitive_prime(prime):
    """
    :param prime: a prime
    :return: returns a random primitive root of this prime
    """
    lst = get_primitive_primes(prime)
    if lst == []:
        return None
    return random.choice(get_primitive_primes(prime))


def get_P_and_G():
    """
    :return: returns a random prime and a random primitive root of that prime
    """
    while True:
        P = random_prime()
        G = random_primitive_prime(P)
        if G is not None:
            return P, G


def get_number():
    """
    :return: returns a random number
    """
    return random.randint(RANDOM_KEY_RANGE[0], RANDOM_KEY_RANGE[1])


def create_key(private_number, key, prime):
    """
    :param private_number: a number
    :param key: a key
    :param prime: a prime
    :return: creates and returns a key based on the parameters
    """
    return int(pow(private_number, key, prime))


def encrypt(message, key):
    """
    :param message: message
    :param key: key
    :return: encryptes/decryptes(with xor) a message with a key and returns it
    """

    # makes the key the same size as the message
    key = str(key)
    if len(key) < len(message):
        x = len(message) // len(key)
        x += 1
        key = key * x
        key = key[:len(message)]
    if len(message) < len(key):
        key = key[:len(message)]

    # encryptes/decryptes
    return "".join([chr(ord(a) ^ ord(b)) for (a, b) in zip(message, key)])
