import socket
import multiprocessing as mp

def chat_listener(nick, auth, channel, output):
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
                parts = line.rstrip().split()
                if parts[0] == "PING":
                    s.send("PONG {0}\r\n".format(parts[1]).encode())
                output.send(line)


if __name__ == '__main__':
    import configparser

    config = configparser.ConfigParser()
    config.read('poetato.ini')

    parent, child = mp.Pipe()
    chat = mp.Process(target = chat_listener,
                      args=(config['twitch']['username'],
                            config['twitch']['token'],
                            config['twitch']['channel'],
                            child))
    chat.start()

    while True:
        print(parent.recv())
