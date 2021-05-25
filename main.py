import time
import json
import telegram.ext
import telegram
import sys
import datetime
import os
import logging
import threading
import six

if six.PY2:
    reload(sys)
    sys.setdefaultencoding('utf8')

Version_Code = 'v1.0.0'

logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
                    )

PATH = os.path.dirname(os.path.realpath(__file__)) + '/'

CONFIG = json.loads(open(PATH + 'config.json', 'r').read())

DATA_LOCK = False

submission_list = json.loads(open(PATH + 'data.json', 'r').read())


def save_data():
    global DATA_LOCK
    while DATA_LOCK:
        time.sleep(0.05)
    DATA_LOCK = True
    f = open(PATH + 'data.json', 'w')
    f.write(json.dumps(submission_list, ensure_ascii=False))
    f.close()
    DATA_LOCK = False


def save_config():
    f = open(PATH + 'config.json', 'w')
    f.write(json.dumps(CONFIG, indent=4))
    f.close()


updater = telegram.ext.Updater(token=os.getenv("bottoken"))
dispatcher = updater.dispatcher

me = updater.bot.get_me()
CONFIG['ID'] = me.id
CONFIG['Username'] = '@' + me.username

print('Starting... (ID: ' + str(CONFIG['ID']) + ', Username: ' + CONFIG['Username'] + ')')


def process_msg(bot, update):
    if update.channel_post != None:
        return
    if update.message.chat_id == CONFIG['Group_ID'] \
        and update.message.reply_to_message != None:
        if update.message.reply_to_message.from_user.id == CONFIG['ID'] \
            and (update.message.reply_to_message.forward_from != None
                 or update.message.reply_to_message.forward_from_chat
                 != None):
            msg = update.message.reply_to_message
            global submission_list
            if submission_list[str(CONFIG['Group_ID']) + ':'
                               + str(msg.message_id)]['posted'] == True:
                return
            if submission_list[str(CONFIG['Group_ID']) + ':'
                               + str(msg.message_id)]['type'] == 'real':
                post = real_name_post(bot, msg,
                        update.message.from_user)
            elif submission_list[str(CONFIG['Group_ID']) + ':'
                                 + str(msg.message_id)]['type'] \
                == 'anonymous':

                post = anonymous_post(bot, msg,
                        update.message.from_user)
            if update.message.text != None:
                bot.send_message(chat_id=CONFIG['Publish_Channel_ID'],
                                 text=update.message.text,
                                 reply_to_message_id=post.message_id)
            return
    if update.message.from_user.id == update.message.chat_id:
        markup = \
            telegram.InlineKeyboardMarkup([[telegram.InlineKeyboardButton("Yes"
                , callback_data='submission_type:real'),
                telegram.InlineKeyboardButton("No",
                callback_data='submission_type:anonymous')],
                [telegram.InlineKeyboardButton("Cancel",
                callback_data='cancel:submission')]])
        if update.message.forward_from != None \
            or update.message.forward_from_chat != None:
            if update.message.forward_from_chat != None:
                markup = \
                    telegram.InlineKeyboardMarkup([[telegram.InlineKeyboardButton("Yes"
                        , callback_data='submission_type:real')],
                        [telegram.InlineKeyboardButton("Cancel",
                        callback_data='cancel:submission')]])
            elif update.message.forward_from.id \
                != update.message.from_user.id:
                markup = \
                    telegram.InlineKeyboardMarkup([[telegram.InlineKeyboardButton("Yes"
                        , callback_data='submission_type:real')],
                        [telegram.InlineKeyboardButton("Cancel",
                        callback_data='cancel:submission')]])
        bot.send_message(chat_id=update.message.chat_id,
                         text="Ready...\n⁠Do you want to keep the source of the message?(aka, do you keep the username of the submitter sender)",
                         reply_to_message_id=update.message.message_id,
                         reply_markup=markup)


def process_command(bot, update):
    if update.channel_post != None:
        return
    command = update.message.text[1:].replace(CONFIG['Username'], ''
            ).lower()
    if command == 'start':
        bot.send_message(chat_id=update.message.chat_id,
                         text="""Acceptable submission types:
Text
Image
Audio/Voice
Video
File""")
        return
    if command == 'version':
        bot.send_message(chat_id=update.message.chat_id,
                         text='Telegram Submission Bot\n'
                         + Version_Code
                         + '\nhttps://github.com/Netrvin/telegram-submission-bot'
                         + '\nhttps://github.com/LakesideMiners/telegram-submission-bot'
                         )
        return
    if update.message.from_user.id == CONFIG['Admin']:
        if command == 'setgroup':
            CONFIG['Group_ID'] = update.message.chat_id
            save_config()
            bot.send_message(chat_id=update.message.chat_id,
                             text="This group has been set as the review group")
            return


def anonymous_post(bot, msg, editor):
    if msg.audio != None:
        r = bot.send_audio(chat_id=CONFIG['Publish_Channel_ID'],
                           audio=msg.audio, caption=msg.caption)
    elif msg.document != None:
        r = bot.send_document(chat_id=CONFIG['Publish_Channel_ID'],
                              document=msg.document,
                              caption=msg.caption)
    elif msg.voice != None:
        r = bot.send_voice(chat_id=CONFIG['Publish_Channel_ID'],
                           voice=msg.voice, caption=msg.caption)
    elif msg.video != None:
        r = bot.send_video(chat_id=CONFIG['Publish_Channel_ID'],
                           video=msg.video, caption=msg.caption)
    elif msg.photo:
        r = bot.send_photo(chat_id=CONFIG['Publish_Channel_ID'],
                           photo=msg.photo[0], caption=msg.caption)
    else:
        r = bot.send_message(chat_id=CONFIG['Publish_Channel_ID'],
                             text=msg.text_markdown,
                             parse_mode=telegram.ParseMode.MARKDOWN)

    submission_list[str(CONFIG['Group_ID']) + ':'
                    + str(msg.message_id)]['posted'] = True
    bot.edit_message_text(text="New Post \nPoster: ["
                          + submission_list[str(CONFIG['Group_ID'])
                          + ':' + str(msg.message_id)]['Sender_Name']
                          + '](tg://user?id='
                          + str(submission_list[str(CONFIG['Group_ID'])
                          + ':' + str(msg.message_id)]['Sender_ID'])
                          + """)
Source: Keep
Reviewers: [""" + editor.name
                          + '](tg://user?id=' + str(editor.id)
                          + ")\nAdopted", chat_id=CONFIG['Group_ID'],
                          parse_mode=telegram.ParseMode.MARKDOWN,
                          message_id=submission_list[str(CONFIG['Group_ID'
                          ]) + ':' + str(msg.message_id)]['Markup_ID'])
    bot.send_message(chat_id=submission_list[str(CONFIG['Group_ID'])
                     + ':' + str(msg.message_id)]['Sender_ID'],
                     text="Your post has been reviewed，Thank you for your submission!",
                     reply_to_message_id=submission_list[str(CONFIG['Group_ID'
                     ]) + ':' + str(msg.message_id)]['Original_MsgID'])
    threading.Thread(target=save_data).start()
    return r


def real_name_post(bot, msg, editor):
    global submission_list
    r = bot.forward_message(chat_id=CONFIG['Publish_Channel_ID'],
                            from_chat_id=CONFIG['Group_ID'],
                            message_id=msg.message_id)

    submission_list[str(CONFIG['Group_ID']) + ':'
                    + str(msg.message_id)]['posted'] = True
    bot.edit_message_text(text="New Post \nPoster: ["
                          + submission_list[str(CONFIG['Group_ID'])
                          + ':' + str(msg.message_id)]['Sender_Name']
                          + '](tg://user?id='
                          + str(submission_list[str(CONFIG['Group_ID'])
                          + ':' + str(msg.message_id)]['Sender_ID'])
                          + """)
source: Keep
Reviewers: [""" + editor.name
                          + '](tg://user?id=' + str(editor.id)
                          + ")\nAdopted", chat_id=CONFIG['Group_ID'],
                          parse_mode=telegram.ParseMode.MARKDOWN,
                          message_id=submission_list[str(CONFIG['Group_ID'
                          ]) + ':' + str(msg.message_id)]['Markup_ID'])
    bot.send_message(chat_id=submission_list[str(CONFIG['Group_ID'])
                     + ':' + str(msg.message_id)]['Sender_ID'],
                     text="Your post has been reviewed，thank you for your submission!",
                     reply_to_message_id=submission_list[str(CONFIG['Group_ID'
                     ]) + ':' + str(msg.message_id)]['Original_MsgID'])
    threading.Thread(target=save_data).start()
    return r


def process_callback(bot, update):
    if update.channel_post != None:
        return
    global submission_list
    query = update.callback_query
    if query.message.chat_id == CONFIG['Group_ID'] and query.data \
        == 'receive:real':
        real_name_post(bot, query.message.reply_to_message,
                       query.from_user)
        return
    if query.message.chat_id == CONFIG['Group_ID'] and query.data \
        == 'receive:anonymous':
        anonymous_post(bot, query.message.reply_to_message,
                       query.from_user)
        return
    if query.data == 'cancel:submission':
        bot.edit_message_text(text="Contribution cancelled",
                              chat_id=query.message.chat_id,
                              message_id=query.message.message_id)
        return
    msg = "New post \nPoster: [" + query.message.reply_to_message.from_user.name \
        + '](tg://user?id=' \
        + str(query.message.reply_to_message.from_user.id) + ")\nSource: "
    fwd_msg = bot.forward_message(chat_id=CONFIG['Group_ID'],
                                  from_chat_id=query.message.chat_id,
                                  message_id=query.message.reply_to_message.message_id)

    submission_list[str(CONFIG['Group_ID']) + ':'
                    + str(fwd_msg.message_id)] = {}

    submission_list[str(CONFIG['Group_ID']) + ':'
                    + str(fwd_msg.message_id)]['posted'] = False

    submission_list[str(CONFIG['Group_ID']) + ':'
                    + str(fwd_msg.message_id)]['Sender_Name'] = \
        query.message.reply_to_message.from_user.name

    submission_list[str(CONFIG['Group_ID']) + ':'
                    + str(fwd_msg.message_id)]['Sender_ID'] = \
        query.message.reply_to_message.from_user.id

    submission_list[str(CONFIG['Group_ID']) + ':'
                    + str(fwd_msg.message_id)]['Original_MsgID'] = \
        query.message.reply_to_message.message_id

    if query.data == 'submission_type:real':
        msg += "Keep"

        submission_list[str(CONFIG['Group_ID']) + ':'
                        + str(fwd_msg.message_id)]['type'] = 'real'
        markup = \
            telegram.InlineKeyboardMarkup([[telegram.InlineKeyboardButton("Use"
                , callback_data='receive:real')]])
        markup_msg = bot.send_message(chat_id=CONFIG['Group_ID'],
                text=msg, reply_to_message_id=fwd_msg.message_id,
                reply_markup=markup,
                parse_mode=telegram.ParseMode.MARKDOWN)

        submission_list[str(CONFIG['Group_ID']) + ':'
                        + str(fwd_msg.message_id)]['Markup_ID'] = \
            markup_msg.message_id
    elif query.data == 'submission_type:anonymous':
        msg += "anonymous"

        submission_list[str(CONFIG['Group_ID']) + ':'
                        + str(fwd_msg.message_id)]['type'] = 'anonymous'
        markup = \
            telegram.InlineKeyboardMarkup([[telegram.InlineKeyboardButton("Use"
                , callback_data='receive:anonymous')]])
        markup_msg = bot.send_message(chat_id=CONFIG['Group_ID'],
                text=msg, reply_to_message_id=fwd_msg.message_id,
                reply_markup=markup,
                parse_mode=telegram.ParseMode.MARKDOWN)

        submission_list[str(CONFIG['Group_ID']) + ':'
                        + str(fwd_msg.message_id)]['Markup_ID'] = \
            markup_msg.message_id
    bot.edit_message_text(text="Thank you for your submission", chat_id=query.message.chat_id,
                          message_id=query.message.message_id)
    threading.Thread(target=save_data).start()


dispatcher.add_handler(telegram.ext.MessageHandler(telegram.ext.Filters.text
                       | telegram.ext.Filters.audio
                       | telegram.ext.Filters.photo
                       | telegram.ext.Filters.video
                       | telegram.ext.Filters.voice
                       | telegram.ext.Filters.document, process_msg))

dispatcher.add_handler(telegram.ext.MessageHandler(telegram.ext.Filters.command,
                       process_command))

dispatcher.add_handler(telegram.ext.CallbackQueryHandler(process_callback))

updater.start_polling()
print('Started')
updater.idle()
print('Stopping...')
save_data()
print('Data saved.')
print('Stopped.')
