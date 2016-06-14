import configparser
import os
import shelve
import tempfile
import urllib.request
import multiprocessing as mp

import chat

def fetch_and_persist_emotes(msg, cache_path, out):
    url = "http://static-cdn.jtvnw.net/emoticons/v1/{0}/1.0"
    cache = shelve.open(cache_path)
    e_to_p = {}
    for e in msg.emotes.keys():
        if e not in cache:
            path, headers = urllib.request.urlretrieve(url.format(e))
            cache[e] = path
        e_to_p[e] = cache[e]
    cache.close()
    msg.localemotes = e_to_p
    out.put(msg)

if __name__ == '__main__':
    config = configparser.ConfigParser()
    config.read('poetato.ini')
    emote_cache = os.path.abspath(
        os.path.join(tempfile.gettempdir(), 'poetato_emotes'))
    messages = mp.Queue()

    chat_i, chat_o = mp.Pipe()
    incoming = mp.Process(target = chat.listen,
                          args=(config['twitch']['username'],
                                config['twitch']['token'],
                                config['twitch']['channel'],
                                chat_o))
    incoming.start()


    while True:
        msg = chat.parse(chat_i.recv())
        fetch_and_persist_emotes(msg, emote_cache, messages)
        print(messages.get())
