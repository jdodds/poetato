import multiprocessing as mp
import chat

if __name__ == '__main__':
    import configparser

    config = configparser.ConfigParser()
    config.read('poetato.ini')

    parent, child = mp.Pipe()
    incoming = mp.Process(target = chat.listen,
                          args=(config['twitch']['username'],
                                config['twitch']['token'],
                                config['twitch']['channel'],
                                child))
    incoming.start()

    while True:
        print(chat.parse(parent.recv()))
