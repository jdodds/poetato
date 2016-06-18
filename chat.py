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
            read_buffer += s.recv(1024).decode(errors='ignore')
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
        localemotes={}
    )


def parse_badges(msg, tag):
    badges = ['staff', 'global_mod', 'admin', 'moderator', 'broadcaster',
              'subscriber', 'turbo']
    for badge in badges:
        if tag.find(badge) >= 0:
            setattr(msg, badge, True)
    return msg


def parse_verbatim(msg, tag):
    verbatims = ['color', 'display-name', 'room-id', 'user-id']
    for v in verbatims:
        if tag.startswith(v):
            cut = "{0}=".format(v)
            attr = v.replace('-', '_')
            setattr(msg, attr, tag.replace(cut, ''))
            break
    return msg


def parse_emotes(msg, tag):
    ems = tag.replace('emotes=', '').split('/')
    for e in filter(None, ems):
        eid, poss = e.split(':')
        for p in filter(None, poss.split(',')):
            start, end = p.split('-')
            msg.emotes[eid].append((int(start), int(end)))
    return msg


def parse(m):
    tag_part, info, command, channel, message = m.split(' ', 4)
    msg = new_message()

    tags = tag_part.split(';')
    for tag in tags:
        if tag.startswith('@badges'):
            msg = parse_badges(msg, tag)
        msg = parse_verbatim(msg, tag)
        if tag.startswith('emotes'):
            msg = parse_emotes(msg, tag)

    msg.channel = channel
    msg.message = message[1:-1]
    return msg
