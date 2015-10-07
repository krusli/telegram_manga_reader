import requests, json

# ----- HTTP failed connections handling -----
# Use a `Session` instance to customize how `requests` handles making HTTP requests.
session = requests.Session()

# `mount` a custom adapter that retries failed connections for HTTP and HTTPS requests.
session.mount("http://", requests.adapters.HTTPAdapter(max_retries=5))
session.mount("https://", requests.adapters.HTTPAdapter(max_retries=5))

# Here, insert the token BotFather gave you for your bot.
token = 
# This is the url for communicating with your bot
url = 'https://api.telegram.org/bot%s/' % token

# -----  functions -----
def send_message(chatid, message):
# function to send messages to chatid.
    i = 0
    while True and i < 5:
        try:
            session.get(url + 'sendMessage', params=dict(chat_id = chatid, text = message))
            break
        except requests.ConnectionError:
            logger.error('ConnectionError', exc_info = True)
            i += 1

def send_message_as_reply(chatid, message, msg_id):
# function to send messages to chatid, reply to msg_id.
    i = 0
    while True and i < 5:
        try:
            session.get(url + 'sendMessage', params=dict(chat_id = chatid, text = message, reply_to_message_id = msg_id))
            break
        except requests.ConnectionError:
            logger.error('ConnectionError', exc_info = True)
            i += 1

def download_file_to_tempfile(url): # http://stackoverflow.com/questions/16694907/how-to-download-large-file-in-python-with-requests-py
    local_filename = 'tempfile.jpg'
    # NOTE the stream=True parameter
    r = requests.get(url, stream=True)
    with open(local_filename, 'wb') as f:
        for chunk in r.iter_content(chunk_size=1024):
            if chunk: # filter out keep-alive new chunks
                f.write(chunk)
                f.flush()
    return


manga_data = {}

def load_manga():
    return (json.loads(requests.get('http://www.mangaeden.com/api/list/0/').text))

# function to get the manga ID from the parsed json response to load_manga()
def get_mangaID(title):
    for entry in manga_list['manga']:
        if entry['t'].lower() == title.lower():
            return entry['i']
    return False

# function to return a list of the chapters of a manga titled title
def list_chapters(title):
    manga_id = get_mangaID(title)
    if manga_id is not False:
        chapters = json.loads(requests.get("http://www.mangaeden.com/api/manga/" + manga_id + "/").text)
        chapter_formatted_list = []
        for entry in chapters['chapters']:
            chapter_formatted_list.append(str(entry[0]) + " - " + str(entry[2]))
        return chapter_formatted_list
    else:
        return ["Manga with the title " + title + " not found."]

def latest_chapter(title):
    manga_id = get_mangaID(title)
    if manga_id is not False:
        chapters = json.loads(requests.get("http://www.mangaeden.com/api/manga/" + manga_id + "/").text)
        chapter_formatted_list = []
        for entry in chapters['chapters']:
            chapter_formatted_list.append(str(entry[0]) + " - " + str(entry[2]))
        return chapter_formatted_list[0]
    else:
        return ["Manga with the title " + title + " not found."]

manga_data = {}

# text.split(), take the x-th index as command, take everything behind it as parameter
def open_manga(title, chapterno, username, chatid, msgid):
    if username not in manga_data.keys():
        manga_data[username] = ['', '' ,''] # current_mangaID, current_chapter, current_page
    manga_ID = get_mangaID(title)
    if manga_ID == False:   # if the manga is not found, tell user and end function
        send_message_as_reply(chatid, "Manga not found.", msgid)
        return
    manga_data[username][0] = manga_ID  # change the manga_ID on file (to be saved later)
    chapter_ID = 0
    chapters = json.loads(requests.get("http://www.mangaeden.com/api/manga/" + manga_ID + "/").text)    # load list of chapters
    for entry in chapters['chapters']:  # search for chapter_ID
        if float(entry[0]) == float(chapterno):  # if a match is found
            chapter_ID = entry[3] # set the variable chapter_ID to be the one the user asked for
            manga_data[username][1] = chapter_ID    # set the chapter_ID on file to be the chapter the user is currently reading
            manga_data[username][2] = 1     # set the page_no to 1 (the user opened a new chapter)
            break
    if chapter_ID == 0:
        send_message_as_reply(chatid, "Chapter not found.", msgid)
    pages = json.loads(requests.get('http://www.mangaeden.com/api/chapter/' + chapter_ID + '/').text)  # list of pages of current manga
    for entry in pages['images']:
        if manga_data[username][2] == entry[0]:
            page_ID = entry[1]
            download_file_to_tempfile('https://cdn.mangaeden.com/mangasimg/' + page_ID)
            session.post(url + 'sendPhoto', data = dict(chat_id=chatid), files=dict(photo = open('tempfile.jpg', 'rb')))
            return

def open_manga_chapter(title, chapterno, username, chatid, msgid):	# opens an entire manga chapter
    if username not in manga_data.keys():
        manga_data[username] = ['', '' ,''] # current_mangaID, current_chapter, current_page
    manga_ID = get_mangaID(title)
    if manga_ID == False:   # if the manga is not found, tell user and end function
        send_message_as_reply(chatid, "Manga not found.", msgid)
        return
    manga_data[username][0] = manga_ID  # change the manga_ID on file (to be saved later)
    chapter_ID = 0
    chapters = json.loads(requests.get("http://www.mangaeden.com/api/manga/" + manga_ID + "/").text)    # load list of chapters
    for entry in chapters['chapters']:  # search for chapter_ID
        if float(entry[0]) == float(chapterno):  # if a match is found
            chapter_ID = entry[3] # set the variable chapter_ID to be the one the user asked for
            manga_data[username][1] = chapter_ID    # set the chapter_ID on file to be the chapter the user is currently reading
            break
    if chapter_ID == 0:
        send_message_as_reply(chatid, "Chapter not found.", msgid)
    pages = json.loads(requests.get('http://www.mangaeden.com/api/chapter/' + chapter_ID + '/').text)  # list of pages of current manga
    for entry in sorted(pages['images']):
        page_ID = entry[1]
        download_file_to_tempfile('https://cdn.mangaeden.com/mangasimg/' + page_ID)
        session.post(url + 'sendPhoto', data = dict(chat_id=chatid), files=dict(photo = open('tempfile.jpg', 'rb')))
        manga_data[username][2] = entry[0]     # set the page_no to 1 (the user opened a new chapter)
    return

def open_manga_next(username, chatid, msgid):
    if username not in manga_data.keys():
        send_message_as_reply(chatid, "use /open to open a manga first.", msgid)
        return
    manga_ID = manga_data[username][0]
    chapter_ID = manga_data[username][1]
    page_no = manga_data[username][2]
    page_no = int(page_no) + 1
    pages = json.loads(requests.get('http://www.mangaeden.com/api/chapter/' + chapter_ID + '/').text)  # list of pages of current manga
    for entry in pages['images']:
        if page_no == entry[0]:
            page_ID = entry[1]
            download_file_to_tempfile('https://cdn.mangaeden.com/mangasimg/' + page_ID)
            session.post(url + 'sendPhoto', data = dict(chat_id=chatid), files=dict(photo = open('tempfile.jpg', 'rb')))
            manga_data[username][2] = page_no #if a match is detected, update last read page no
            return
    # if return not executed, page not found
    send_message_as_reply(chatid, "You have reached the end of the chapter. Open a new chapter", msgid)

def open_manga_prev(username, chatid, msgid):
    if username not in manga_data.keys():
        send_message_as_reply(chatid, "use /open to open a manga first.", msgid)
        return
    manga_ID = manga_data[username][0]
    chapter_ID = manga_data[username][1]
    page_no = manga_data[username][2]
    page_no = int(page_no) - 1
    pages = json.loads(requests.get('http://www.mangaeden.com/api/chapter/' + chapter_ID + '/').text)  # list of pages of current manga
    for entry in pages['images']:
        if page_no == entry[0]:
            page_ID = entry[1]
            download_file_to_tempfile('https://cdn.mangaeden.com/mangasimg/' + page_ID)
            session.post(url + 'sendPhoto', data = dict(chat_id=chatid), files=dict(photo = open('tempfile.jpg', 'rb')))
            manga_data[username][2] = page_no #if a match is detected, update last read page no
            return
    # if return not executed, page not found
    send_message_as_reply(chatid, "You have reached the start of the chapter. Open a new chapter", msgid)

def open_manga_jump(username, chatid, msgid, jump):
    if username not in manga_data.keys():
        send_message_as_reply(chatid, "use /open to open a manga first.", msgid)
        return
    manga_ID = manga_data[username][0]
    chapter_ID = manga_data[username][1]
    page_no = int(jump)
    pages = json.loads(requests.get('http://www.mangaeden.com/api/chapter/' + chapter_ID + '/').text)  # list of pages of current manga
    for entry in pages['images']:
        if page_no == entry[0]:
            page_ID = entry[1]
            download_file_to_tempfile('https://cdn.mangaeden.com/mangasimg/' + page_ID)
            session.post(url + 'sendPhoto', data = dict(chat_id=chatid), files=dict(photo = open('tempfile.jpg', 'rb')))
            manga_data[username][2] = page_no # if a match is detected, update last read page no
            return
    # if return not executed, page not found
    send_message_as_reply(chatid, "Page not found.", msgid)

# load MangaEden's list of manga
manga_list = load_manga()

# admin list
admin = [] % insert admin usernames here

# This will load the last update we've checked, so as to not pass old messages through the bot
try:
    with open('last_update.txt', 'r') as f:
        last_update = int(f.readline().strip())
except FileNotFoundError:
    last_update = 0

while True:
    # My chat is up and running, I need to maintain it! Get me all chat updates
    try:
        get_updates = json.loads(requests.get(url + 'getUpdates', dict(offset=last_update)).text)
    except ConnectionError:
        pass
    # Ok, I've got 'em. Let's iterate through each one
    for update in get_updates['result']:
        # First make sure I haven't read this update yet
        if last_update < update['update_id']:
            last_update = update['update_id']
            # I've got a new update!
            # Write the value for last_update to file
            with open('last_update.txt', 'w') as f2:
                f2.write(str(last_update))
            if 'text' in update['message'].keys():
                try:
                    if update['message']['text'].startswith("/listchapters "):
                        words = update['message']['text'].split()
                        try:
                             send_message_as_reply(update['message']['chat']['id'], '\n'.join(list_chapters(' '.join(words[1:]))), update['message']['message_id'])
                        except IndexError:
                            send_message_as_reply(update['message']['chat']['id'], "Incorrect syntax. The correct syntax is > /listchapters shigatsu wa kimi no uso", update['message']['message_id'])
                    if update['message']['text'].startswith("/latestchapter "):
                        words = update['message']['text'].split()
                        try:
                             send_message_as_reply(update['message']['chat']['id'], latest_chapter(' '.join(words[1:])), update['message']['message_id'])
                        except IndexError:
                            send_message_as_reply(update['message']['chat']['id'], "Incorrect syntax. The correct syntax is > /listchapters shigatsu wa kimi no uso", update['message']['message_id'])
                    if update['message']['text'].startswith("/open "):
                        words = update['message']['text'].split()
                        try:
                            open_manga(' '.join(words[1:-1]), words[-1], update['message']['from']['username'], update['message']['chat']['id'], update['message']['message_id'])
                        except IndexError:
                            send_message_as_reply(update['message']['chat']['id'], "Incorrect syntax. The correct syntax is > /readmanga open shigatsu wa kimi no uso 1", update['message']['message_id'])
                    if update['message']['text'].startswith("/next"):
                        open_manga_next(update['message']['from']['username'], update['message']['chat']['id'], update['message']['message_id'])
                    if update['message']['text'].startswith("/prev"):
                        open_manga_prev(update['message']['from']['username'], update['message']['chat']['id'], update['message']['message_id'])
                    if update['message']['text'].startswith("/jump "):
                        words = update['message']['text'].split()
                        try:
                            open_manga_jump(update['message']['from']['username'], update['message']['chat']['id'], update['message']['message_id'], words[1])
                        except IndexError:
                            send_message_as_reply(update['message']['chat']['id'], "Incorrect syntax. The correct syntax to jump to page n is > /readmanga jump n", update['message']['message_id'])
                    if update['message']['text'].startswith("/openchapter "):
                        words = update['message']['text'].split()
                        try:
                            open_manga_chapter(' '.join(words[1:-1]), words[-1], update['message']['from']['username'], update['message']['chat']['id'], update['message']['message_id'])
                        except IndexError:
                            send_message_as_reply(update['message']['chat']['id'], "Incorrect syntax. The correct syntax is > /readmanga open shigatsu wa kimi no uso 1", update['message']['message_id'])
                    if update['message']['text'].startswith("/status"):
                        send_message(update['message']['chat']['id'], "I'm up and running!")

                    if update['message']['from']['username'] in admin:
                        if update['message']['text'].startswith("/poweroff"):
                            send_message(update['message']['chat']['id'], "Powering off.")
                            sys.exit(0)
                except SystemExit:
                    sys.exit(0)
                except ConnectionError:
                    pass
                except Exception:
                    pass
