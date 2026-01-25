users = {}
sid_to_user = {}
message_history  = {}

def get_room_id(user1,user2):
    return "_".join(sorted([user1,user2]))