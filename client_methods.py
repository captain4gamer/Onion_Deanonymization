import random
import string

NAMES = ['Michael', 'Christopher', 'Jessica', 'Matthew', 'Ashley', 'Jennifer', 'Joshua', 'Amanda', 'Daniel', 'David', 'James', 'Robert', 'John', 'Joseph', 'Andrew', 'Ryan', 'Brandon', 'Jason', 'Justin', 'Sarah', 'William', 'Jonathan', 'Stephanie', 'Brian', 'Nicole', 'Nicholas', 'Anthony', 'Heather', 'Eric', 'Elizabeth', 'Adam', 'Megan', 'Melissa', 'Kevin', 'Steven', 'Thomas', 'Timothy', 'Christina', 'Kyle', 'Rachel', 'Laura', 'Lauren', 'Amber', 'Brittany', 'Danielle', 'Richard', 'Kimberly', 'Jeffrey', 'Amy', 'Crystal', 'Michelle', 'Tiffany', 'Jeremy', 'Benjamin', 'Mark', 'Emily', 'Aaron', 'Charles', 'Rebecca', 'Jacob', 'Stephen', 'Patrick', 'Sean', 'Erin', 'Zachary', 'Jamie', 'Kelly', 'Samantha', 'Nathan', 'Sara', 'Dustin', 'Paul', 'Angela', 'Tyler', 'Scott', 'Katherine', 'Andrea', 'Gregory', 'Erica', 'Mary', 'Travis', 'Lisa', 'Kenneth', 'Bryan', 'Lindsey', 'Kristen', 'Jose', 'Alexander', 'Jesse', 'Katie', 'Lindsay', 'Shannon', 'Vanessa', 'Courtney', 'Christine', 'Alicia', 'Cody', 'Allison', 'Bradley', 'Samuel']
LAST_NAMES = ['Chung', 'Chen', 'Melton', 'Hill', 'Puckett', 'Song', 'Hamilton', 'Bender', 'Wagner', 'McLaughlin', 'McNamara', 'Raynor', 'Moon', 'Woodard', 'Desai', 'Wallace', 'Lawrence', 'Griffin', 'Dougherty', 'Powers', 'May', 'Steele', 'Teague', 'Vick', 'Gallagher', 'Solomon', 'Walsh', 'Monroe', 'Connolly', 'Hawkins', 'Middleton', 'Goldstein', 'Watts', 'Johnston', 'Weeks', 'Wilkerson', 'Barton', 'Walton', 'Hall', 'Ross', 'Woods', 'Mangum', 'Joseph', 'Rosenthal', 'Bowden', 'Underwood', 'Jones', 'Baker', 'Merritt', 'Cross', 'Cooper', 'Holmes', 'Sharpe', 'Morgan', 'Hoyle', 'Allen', 'Rich', 'Grant', 'Proctor', 'Diaz', 'Graham', 'Watkins', 'Hinton', 'Marsh', 'Hewitt', 'Branch', "O'Brien", 'Case', 'Christensen', 'Parks', 'Hardin', 'Lucas', 'Eason', 'Davidson', 'Whitehead', 'Rose', 'Sparks', 'Moore', 'Pearson', 'Rodgers', 'Graves', 'Scarborough', 'Sutton', 'Sinclair', 'Bowman', 'Olsen', 'Love', 'McLean', 'Christian', 'Lamb', 'James', 'Chandler', 'Stout', 'Cowan', 'Golden', 'Bowling', 'Beasley', 'Clapp', 'Abrams', 'Tilley']
PASSWORD_LENGTH = 10


def generate_messages_for_server():
    """
    :return: generates a name,last name, phone number and a password for a client
    """

    # generate name
    name = random.choice(NAMES)

    # generate last name
    last_name = random.choice(LAST_NAMES)

    # generate phone
    phone_number = ""
    for i in range(10):
        phone_number += str(random.randint(0, 9))

    # generate password
    characters = list(string.ascii_lowercase + string.ascii_uppercase + string.digits)
    password = ""
    for i in range(PASSWORD_LENGTH):
        password += random.choice(characters)

    return [name, last_name, phone_number, password]
