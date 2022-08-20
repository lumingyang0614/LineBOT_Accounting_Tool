import os
import re
import json
import random
from dotenv import load_dotenv
from pyquery import PyQuery
from fastapi import FastAPI, Request, HTTPException
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import *
from influxdb import InfluxDBClient
load_dotenv() # Load your local environment variables


CHANNEL_TOKEN = os.environ.get('LINE_TOKEN')
CHANNEL_SECRET = os.getenv('LINE_SECRET')

app = FastAPI()

My_LineBotAPI = LineBotApi(CHANNEL_TOKEN) # Connect Your API to Line Developer API by Token
handler = WebhookHandler(CHANNEL_SECRET) # Event handler connect to Line Bot by Secret key

CHANNEL_ID = os.getenv('LINE_UID') # For any message pushing to or pulling from Line Bot using this ID
class DB():
    def __init__(self, ip, port, user, password, db_name):
        self.client = InfluxDBClient(ip, port, user, password, db_name) 
        print('Influx DB init.....')

    def insertData(self, data):
        if self.client.write_points(data):
            return True
        else:
            print('Falied to write data')
            return False

    def queryData(self, query):
        return self.client.query(query)
db = DB('127.0.0.1', 8086, 'root', '', 'M11115Q04')
# Create my emoji list
my_emoji = [
    [{'index':27, 'productId':'5ac1bfd5040ab15980c9b435', 'emojiId':'005'}],
    [{'index':27, 'productId':'5ac1bfd5040ab15980c9b435', 'emojiId':'019'}],
    [{'index':27, 'productId':'5ac1bfd5040ab15980c9b435', 'emojiId':'096'}]
]
my_event = ['#help','#note', '#report','#delete','#statistics']
# Line Developer Webhook Entry Point
@app.post('/')
async def callback(request: Request):
    body = await request.body() # Get request
    signature = request.headers.get('X-Line-Signature', '') # Get message signature from Line Server
    try:
        handler.handle(body.decode('utf-8'), signature) # Handler handle any message from LineBot and 
    except InvalidSignatureError:
        raise HTTPException(404, detail='LineBot Handle Body Error !')
    return 'OK'

# All message events are handling at here !
@handler.add(MessageEvent, message=TextMessage)
def handle_textmessage(event):
    recieve_message = str(event.message.text).split(' ')
    # Get first splitted message as command
    case_ = recieve_message[0].lower().strip()
    # Case 1: get pokemon
    if recieve_message[0].isdigit():
        if(recieve_message[2].isdigit()):
            strcal = recieve_message[1] 
            if(strcal == '+'):
                ans = int(recieve_message[0]) + int(recieve_message[2])
                My_LineBotAPI.reply_message(
                    event.reply_token,
                    TextSendMessage(text=ans)
                )
            elif(strcal == '*'):
                ans = int(recieve_message[0]) * int(recieve_message[2])
                My_LineBotAPI.reply_message(
                    event.reply_token,
                    TextSendMessage(text=ans)
                )
            elif(strcal == '-'):
                ans = int(recieve_message[0]) - int(recieve_message[2])
                My_LineBotAPI.reply_message(
                    event.reply_token,
                    TextSendMessage(text=ans)
                )
            elif(strcal == '/'):
                if(recieve_message[2] != '0'):
                    ans = int(recieve_message[0]) / int(recieve_message[2])
                    My_LineBotAPI.reply_message(
                        event.reply_token,
                        TextSendMessage(text=ans)
                    )
                else:
                    My_LineBotAPI.reply_message(
                        event.reply_token,
                        TextSendMessage(text='b can not be 0 ')
                    )
            else:
                My_LineBotAPI.reply_message(
                    event.reply_token,
                    TextSendMessage(text='Error, please try again. #help have Directions')

                )
        else:
            My_LineBotAPI.reply_message(
                event.reply_token,
                TextSendMessage(text='Error, please try again. #help have Directions')
            )
    elif re.match(my_event[0], case_):
        command_describtion = '$ Directions\n\
        A is first number\n\
        B is second number\n\
        A + B -->A plus B\n\
        A - B -->A minus B\n\
        A * B -->A multiply B\n\
        #note [事件] [+/-] [錢]\n\
        #delete [事件]\n\
        #report \n\
        #sum \n'
        My_LineBotAPI.reply_message(
            event.reply_token,
            TextSendMessage(
                text=command_describtion,
                emojis=[
                    {
                        'index':0,
                        'productId':'5ac21a18040ab15980c9b43e',
                        'emojiId':'110'
                    }
                ]
            )
        )
    elif re.match(my_event[1], case_):
        # cmd: #note [事件] [+/-] [錢]
        event_ = recieve_message[1]
        op = recieve_message[2]
        money = int(recieve_message[3])
        # process +/-
        if op == '-':
            money *= -1
        # get user id
        user_id = event.source.user_id
        
        # build data
        data = [
            {
                "measurement" : "accounting_items",
                "tags": {
                    "user": str(user_id),
                    "e" : str(event_
                },
                "fields":{
                    "event": str(event_),
                    "money": money
                }
            }
        ]
        if db.insertData(data):
            # successed
            My_LineBotAPI.reply_message(
                event.reply_token,
                TextSendMessage(
                    text="Write to DB Successfully!"
                )
            )
    elif re.match(my_event[2], case_):
        # get user id
        user_id = event.source.user_id
        query_str = """
        select * from accounting_items 
        """
        result = db.queryData(query_str)
        points = result.get_points(tags={'user': str(user_id)})
        
        reply_text = ''
        for i, point in enumerate(points):
            time = point['time']
            event_ = point['event']
            money = point['money']
            reply_text += f'[{i}] -> [{time}] : {event_}   {money}\n'

        My_LineBotAPI.reply_message(
            event.reply_token,
            TextSendMessage(
                text=reply_text
            )
        )
    elif re.match(my_event[3], case_):
        user_id = event.source.user_id
        #https://stackoverflow.com/questions/39685114/delete-points-with-unwanted-field-values-from-influxdb-measuremen
        db.queryData(f'SELECT * INTO metrics_clean FROM accounting_items WHERE event != \'{recieve_message[1]}\' GROUP BY * ')
        # Drop existing dirty measurement
        db.queryData('DROP measurement accounting_items')
        # Copy temporary measurement to existing measurement
        db.queryData("SELECT * INTO accounting_items FROM metrics_clean GROUP BY * ")
        db.queryData('DROP measurement metrics_clean')
        My_LineBotAPI.reply_message(
            event.reply_token,
            TextSendMessage(
                text= "delete complete"
            )
        )
    elif re.match(my_event[4], case_):

        user_id = event.source.user_id
        query_str = """
        select * from accounting_items WHERE time < 
        """
        result = db.queryData(query_str)
        points = result.get_points(tags={'user': str(user_id)})
        
        reply_text = ''
        for i, point in enumerate(points):
            time = point['time']
            event_ = point['event']
            money = point['money']
            reply_text += f'[{i}] -> [{time}] : {event_}   {money}\n'

        My_LineBotAPI.reply_message(
            event.reply_token,
            TextSendMessage(
                text="Over"
            )
        )
    else:
        My_LineBotAPI.reply_message(
            event.reply_token,
            TextSendMessage(
                text='$ Welcome ! #help have directions',
                emojis=[
                    {
                        'index':0,
                        'productId':'5ac2213e040ab15980c9b447',
                        'emojiId':'035'
                    }
                ]
            )
        )

# Line Sticker Class
class My_Sticker:
    def __init__(self, p_id: str, s_id: str):
        self.type = 'sticker'
        self.packageID = p_id
        self.stickerID = s_id

'''
See more about Line Sticker, references below
> Line Developer Message API, https://developers.line.biz/en/reference/messaging-api/#sticker-message
> Line Bot Free Stickers, https://developers.line.biz/en/docs/messaging-api/sticker-list/
'''
# Add stickers into my_sticker list
my_sticker = [My_Sticker(p_id='446', s_id='1995'), My_Sticker(p_id='446', s_id='2012'),
     My_Sticker(p_id='446', s_id='2024'), My_Sticker(p_id='446', s_id='2027'),
     My_Sticker(p_id='789', s_id='10857'), My_Sticker(p_id='789', s_id='10877'),
     My_Sticker(p_id='789', s_id='10881'), My_Sticker(p_id='789', s_id='10885'),
     ]

# Line Sticker Event
@handler.add(MessageEvent, message=StickerMessage)
def handle_sticker(event):
    # Random choice a sticker from my_sticker list
    ran_sticker = random.choice(my_sticker)
    # Reply Sticker Message
    My_LineBotAPI.reply_message(
        event.reply_token,
        StickerSendMessage(
            package_id= ran_sticker.packageID,
            sticker_id= ran_sticker.stickerID
        )
    )
if __name__ == '__main__':
    import uvicorn
    uvicorn.run(app='main:app', reload=True, host='0.0.0.0', port=8787)
    uvicorn.run(app='main:app', reload=True, host='0.0.0.0', port=8086)