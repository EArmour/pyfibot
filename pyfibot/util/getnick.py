
def get(user):
    nick = user[0:user.find('!')]
    
    return nick