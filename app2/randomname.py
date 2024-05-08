import random
import string

def generate_random_name(length=7):
    name = ''
    characters = string.ascii_lowercase + string.digits
    for _ in range(length):
        name =  name + (random.choice(characters))

    return name+"@rapidalias.xyz"
    