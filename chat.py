import socket
from collections import defaultdict
from types import SimpleNamespace

def listen(nick, auth, channel, output):
    host = 'irc.twitch.tv'
    port = 6667

    with socket.socket() as s:
        s.connect((host, port))
        s.send("PASS {0}\r\n".format(auth).encode())
        s.send("NICK {0}\r\n".format(nick).encode())
        s.send("JOIN #{0}\r\n".format(channel).encode())
        s.send("CAP REQ :twitch.tv/tags\r\n".encode())

        read_buffer = ""
        while True:
            read_buffer += s.recv(1024).decode()
            temp = read_buffer.split("\n")
            read_buffer = temp.pop()

            for line in temp:
                if line.startswith("PING"):
                    s.send("PONG :tmi.twitch.tv\r\n".encode())
                if line.find("PRIVMSG") >= 0:
                    output.send(line)


def new_message():
    return SimpleNamespace(
        staff=False,
        admin=False,
        global_mod=False,
        moderator=False,
        subscriber=False,
        turbo=False,
        broadcaster=False,
        color='',
        display_name='',
        emotes=defaultdict(list),
        room_id=0,
        user_id=0,
        user_type='',
        channel='',
        message='',
    )

def parse(m):
    tag_part, info, command, channel, message = m.split(' ', 4)
    msg = new_message()

    tags = tag_part.split(';')
    for tag in tags:
        if tag.startswith('@badges'):
            if tag.find('staff') >=0:
                msg.staff = True
            if tag.find('global_mod') >= 0:
                msg.global_mod = True
            if tag.find('admin') >= 0:
                msg.admin = True
            if tag.find('moderator') >= 0:
                msg.moderator = True
            if tag.find('broadcaster') >= 0:
                msg.broadcaster = True
            if tag.find('subscriber') >= 0:
                msg.subscriber = True
            if tag.find('turbo') >= 0:
                msg.turbo = True
        if tag.startswith('color'):
            msg.color = tag.replace('color=', '')
        if tag.startswith('display-name'):
            msg.display_name = tag.replace('display-name=', '')
        if tag.startswith('room-id'):
            msg.room_id = tag.replace('room-id=', '')
        if tag.startswith('user-id'):
            msg.user_id = tag.replace('user-id=', '')
        if tag.startswith('emotes'):
            ems = tag.replace('emotes=', '').split('/')
            for e in filter(None, ems):
                eid, poss = e.split(':')
                for p in filter(None, poss.split(',')):
                    start, end = p.split('-')
                    msg.emotes[eid].append((int(start), int(end)))
    msg.channel = channel
    msg.message = message[1:-1]
    return msg
