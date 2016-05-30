import requests, json, csv, random, os, multiprocessing, html, time, os

# URL and auth token for bot requests
token =  # enter the API token from BotFather here
url = 'https://api.telegram.org/bot%s/' % token

# Create a `Session` instance to customize how `requests` handles making HTTP requests.
session = requests.Session()

# `mount` a custom adapter that retries failed connections for HTTP and HTTPS requests.
session.mount("http://", requests.adapters.HTTPAdapter(max_retries=5))
session.mount("https://", requests.adapters.HTTPAdapter(max_retries=5))

class send_class:
    def message(self, chatid, message_text):
        requests.get(url + 'sendMessage', params = dict(chat_id = chatid, \
            text = message_text))
    def message_reply(self, chatid, message_text, message_id):
        requests.get(url + 'sendMessage', params = dict(chat_id = chatid, \
            text = message_text, reply_to_message_id = message_id))
    def markdown(self, chatid, message_text):
        requests.get(url + 'sendMessage', params = dict(chat_id = chatid, \
            text = message_text, parse_mode = 'Markdown'))
    def markdown_reply(self, chatid, message_text, message_id):
        requests.get(url + 'sendMessage', params = dict(chat_id = chatid, \
            text = message_text, reply_to_message_id = message_id, \
            parse_mode = 'Markdown'))
    def action(self, chatid, bot_action):
        requests.get(url + 'sendChatAction', params = dict(chat_id = chatid, \
            action = bot_action))
    def send_photo(self, chatid, filename):
        self.action(chatid, 'upload_photo')
        session.post(url + 'sendPhoto', data = dict(chat_id = chatid), \
            files = dict(photo = open(filename, 'rb')))
    def send_document(self, chatid, filename):
        self.action(chatid, 'upload_document')
        session.post(url + 'sendDocument', data = dict(chat_id = chatid), \
            files = dict(document = open(filename, 'rb')))
send = send_class()

def download_file_to_tempfile(url):
    r = requests.get(url, stream=True)

    # if file exists, create another file as to not disrupt other processes
    filename = 'tempfile'
    if filename + '.jpg' in os.listdir('.'):
        while True:
            filename += str(random.randint(1,10))
            if filename + '.jpg' not in os.listdir('.'):
                break
    filename += '.jpg'

    with open(filename, 'wb') as f:
        for chunk in r.iter_content(chunk_size=1024):
            if chunk: # filter out keep-alive new chunks
                f.write(chunk)
                f.flush()

    return filename

# ----- MangaEden reader -----
class manga_class:
    manga_list_url = 'http://www.mangaeden.com/api/list/0/'
    manga_chapters_url = "http://www.mangaeden.com/api/manga/"
    manga_pages_url = 'http://www.mangaeden.com/api/chapter/'
    manga_image_url = 'https://cdn.mangaeden.com/mangasimg/'

    def load_manga(self):
        return (json.loads(requests.get(manga_list_url).text))
    def get_mangaID(self, title): # get manga_id from load_manga() JSON response
        for entry in self.manga_list['manga']:
            if entry['t'].lower() == title.lower():
                return entry['i']
        return False
    def get_title(self, title):
        for entry in self.manga_list['manga']:
            if entry['t'].lower() == title.lower():
                return entry['t']
    def list_chapters(self, title):
        manga_id = self.get_mangaID(title)
        if manga_id is not False:
            chapters = json.loads(requests.get(manga_chapters_url \
                + manga_id + "/").text)
            chapter_formatted_list = []
            for entry in chapters['chapters']:
                if entry[2] == None:
                    chapter_formatted_list.append(str(entry[0]) + ": -")
                else:
                    chapter_formatted_list.append(str(entry[0]) + ": " + \
                        html.unescape(str(entry[2])))
            return [chapter_formatted_list[i:i+100] \
                for i in range(0,len(chapter_formatted_list), 100)]
        else:
            return ["Manga with the title " + title + " not found."]
    def latest_chapter(self, title):
        manga_id = self.get_mangaID(title)
        if manga_id is not False:
            chapters = json.loads(requests.get(manga_chapters_url \
                + manga_id + "/").text)
            chapter_formatted_list = []
            for entry in chapters['chapters']:
                chapter_formatted_list.append(str(entry[0]) + ": " \
                    + html.unescape(str(entry[2])))
            return str(chapter_formatted_list[0])
        else:
            return "Manga with the title " + title + " not found."

    def manga_info(self, title):
        manga_id = self.get_mangaID(title)
        if manga_id is not False:
            title_data = json.loads(requests.get(manga_chapters_url \
                + manga_id + "/").text)
            genres = []
            for entry in title_data['categories']:
                genres.append(entry)
            title = self.get_title(title)    # get mangaeden title
            author = title_data['author']
            genres = ", ".join(genres) # convert list to comma separated string
            synopsis = html.unescape(title_data['description'])
            output_string = "*" + title + "* - " + author + "\n\n"
            output_string += "_Genres_\n"
            output_string += genres + "\n\n"
            output_string += "_Synopsis_\n"
            output_string += synopsis
            return output_string
        else:
            return "Manga with the title " + title + " not found."

    # opens an entire manga chapter, sends each photo to chatid
    def open_manga_chapter(self, title, chapterno, chatid, msgid):
        manga_ID = self.get_mangaID(title)
        # if the manga is not found, tell user and exit
        if manga_ID == False:
            send.message_reply(chatid, "Manga with the title " + title \
                + " not found.", msgid)
            return

        try: # check if chapter number is valid
            float(chapterno)
        except ValueError:
            send.message_reply(chatid, "Please enter a chapter number.", msgid)
            return

        chapter_ID = 0
        manga_chapters = json.loads(requests.get(manga_chapters_url \
            + manga_ID + "/").text)
        for entry in manga_chapters['chapters']:
            if float(entry[0]) == float(chapterno):
                chapter_ID = entry[3]
                break

        if chapter_ID == 0:
            send.message_reply(chatid, "Chapter not found.", msgid)
        else:
            # list of pages of current manga
            pages = json.loads(requests.get(manga_pages_url \
                + chapter_ID + '/').text)
            for entry in sorted(pages['images']):
                page_ID = entry[1]
                filename = download_file_to_tempfile(manga_image_url \
                    + page_ID)
                send.send_photo(chatid, filename)
                os.remove(filename)
            return

manga = manga_class()
manga.manga_list = manga.load_manga()

# ----- main bot code block -----
class message:
    pass

class inline_query:
    pass

def main():
    # ----- operating variables -----
    # get last_update, so bot can request messages after a certain update ID.
    try:
        with open('last_update.txt', 'r') as f:
            last_update = int(f.readline().strip())
    except FileNotFoundError:
        last_update = 0

    # create a multiprocessing Pool
    pool = multiprocessing.Pool(processes = 4)

    while True:
        try:
            get_updates = json.loads(requests.get(url + 'getUpdates', \
                dict(offset = last_update)).text)
        except ConnectionError:
            pass

        for update in get_updates['result']:
            if last_update < update['update_id']:
                last_update = update['update_id']

                # write last_update to file (ID of last 'update' received)
                with open('last_update.txt', 'w') as f:
                    f.write(str(last_update))

                # check if message or inline_query
                if 'message' in update.keys():
                    message.message_id = update['message']['message_id']
                    message.chat_id = update['message']['chat']['id']
                    message.sender = update['message']['from']

                    if 'text' in update['message'].keys():
                        message.text = update['message']['text']
                        try:
                            if message.text.startswith('/status'):
                                send.message(message.chat_id, "I'm up and running!")

                            if message.text.startswith('/latestchapter'):
                                try:
                                    syntax_test = message.text.split()[1]
                                    message.text = message.text[15:]
                                    send.message(message.chat_id, manga.latest_chapter(message.text))
                                except IndexError:
                                    send.message_reply(message.chat_id, "Please use the correct format for the function. Example: /latestchapter gintama", message.message_id)
                            if message.text.startswith('/listchapters'):
                                try:
                                    syntax_test = message.text.split()[1]
                                    message.text = message.text[14:]
                                    for sublist in manga.list_chapters(message.text):
                                        send.message(message.chat_id, '\n'.join(sublist))
                                except IndexError:
                                    send.message_reply(message.chat_id, "Please use the correct format for the function. Example: /listchapters gintama", message.message_id)
                            if message.text.startswith('/openchapter'):
                                try:
                                    words = message.text.split()[1:]
                                    syntax_test = words[1]
                                    # create asynchronous worker process
                                    pool.apply_async(manga.open_manga_chapter, (' '.join(words[0:-1]), words[-1], message.chat_id, message.message_id))
                                except IndexError:
                                    send.message_reply(message.chat_id, 'Please use the correct format for /openchapter.\nExample: /openchapter gintama 1', message.message_id)
                            if message.text.startswith('/mangainfo'):
                                try:
                                    syntax_test = message.text.split()[1]
                                    message.text = message.text[11:]
                                    send.markdown(message.chat_id, manga.manga_info(message.text))
                                except IndexError:
                                    send.message_reply(message.chat_id, "Please use the correct format for the function. Example: /mangainfo gintama", message.message_id)


                        except SystemExit:
                            sys.exit(0)
                        except ConnectionError:
                            pass

                elif 'inline_query' in update.keys():
                    pass

if __name__ == "__main__":
    main()
