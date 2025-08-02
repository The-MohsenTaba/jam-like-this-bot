import logging
from telegram import Update,ReplyKeyboardMarkup, KeyboardButton,ReplyKeyboardRemove
from telegram.ext import ApplicationBuilder, ContextTypes, CommandHandler , MessageHandler ,filters
from tracklist import get_track_list , ft_remover
import requests
import asyncio
from openai import AsyncOpenAI
import os
from dotenv import load_dotenv

load_dotenv()

# Defining our ai client with AsyncOpenAI
client = AsyncOpenAI(
    api_key=os.getenv('AI_API_KEY'),
    base_url="https://openrouter.ai/api/v1"
)



logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """ Handling the /start command , and defining keyboards """

    keyboard = [
        [KeyboardButton("🛑 Stop Recommending")],
        [KeyboardButton("ℹ️ Help")]
    ]
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    await context.bot.send_message(chat_id=update.effective_chat.id,
                                    text="🎵 Send me a song name for recommendations!",
                                    reply_markup=reply_markup
                                   )
    

async def get_music(update:Update , context: ContextTypes.DEFAULT_TYPE):
    """ Getting music list and for each music calling api for available Demo! """

    music_list = context.user_data['music_list']
    chat_id = context.user_data['chat_id']

    for music in music_list:
        # Check for cancellation every iteration
        if 'music_task' in context.user_data and context.user_data['music_task'].cancelled():
            return
        music = music.replace("\"","")
        song , artist = music.split('-',1)
        song = song[2:]
        song = ft_remover(song).strip()
        artist = ft_remover(artist).strip()
        try:
            # calling deezer api for getting music demo
            response=requests.get(
                f'https://api.deezer.com/search?q=artist:"{artist}" track:"{song}"'
            )
            deezer_response = response.json()

            if deezer_response.get('data'):
                obj = deezer_response['data'][0]
                print('this is the object we have !',obj)
                # Send the preview MP3 (30-second clips are freely available)
                await context.bot.send_audio(chat_id=chat_id ,audio=obj['preview'],
                                            performer= f"{obj['artist']['name']}",
                                            title= f"{obj['title']}(DEMO)",
                                            caption= f"🎵 {music} (DEMO)",
                                            reply_markup=ReplyKeyboardMarkup([["🛑 Stop Recommending"]], resize_keyboard=True))
            else:
                await context.bot.send_message(chat_id=chat_id, text=f"{music} \n (Couldn't Find a Demo for you 🦧 )",
                                                reply_markup=ReplyKeyboardMarkup([["🛑 Stop Recommending"]], resize_keyboard=True))
            await asyncio.sleep(3)
        # probebly wont happen at all
        except Exception as e:
            await context.bot.send_message(chat_id=chat_id , text=f"{music} \n (Couldn't Find a Demo for you 🦧 )",
                                            reply_markup=ReplyKeyboardMarkup([["🛑 Stop Recommending"]], resize_keyboard=True))
    await context.bot.send_message(chat_id=chat_id, text=f"🎶 There you go!\n I hope you enjoy this playlist 😇",reply_markup=ReplyKeyboardRemove())

async def api_call(input_song,update:Update,context: ContextTypes.DEFAULT_TYPE):
    """ sending a prompt to your AI api and gets the result """

    prompt = f"you are a expert music nerd who thinks and analyze musics deeply . i give you a music name and i want you to suggest me 5 similar song , considering many factors like : text and lyrics , vibe , mood , music genre , releasing date , music structure , tempo, concept and ... . concept ,mood , vibe and lyrics are must be similar and they are the most important factor  i want you analyze , but keep your suggestions in a same structure and tempo !. give me 5 music that are similar to <{input_song}> . please JUST send me a list of songs , no additional eplains ! like this format 1.SONG-ARTIST /n 2.SONG-ARTIST /n ..."
    # stop ai generation if user wants to cancel operation
    cancelled=context.user_data['api_call'].cancelled() 
    if not(cancelled ):
        completion = await client.chat.completions.create(
                model="deepseek/deepseek-r1-0528:free",
                messages=[
                    {
                "role": "user",
                "content": prompt
                    }
                ]
            )
        # small sleeps to let api call task change (if there was any changes)
        await asyncio.sleep(3)
        context.user_data['api_answer']= completion.choices[0].message.content
        cancelled=context.user_data['api_call'].cancelled()

        music_list = context.user_data['api_answer']

        # sometimes ai returns invalid answers that conflicts the process ! we check if ai answer is in the correct format
        if not music_list.startswith('1.'):
            await context.bot.send_message(chat_id=update.effective_chat.id , text=f" Something went wrong! please try again 🥺💔",reply_markup=ReplyKeyboardMarkup([["ℹ️ Help"]], resize_keyboard=True))
            return
        track_list =get_track_list(music_list)
        context.user_data['music_list']=track_list

        # building a new music task to pass it the list . 
        context.user_data['music_task'] = asyncio.create_task(
            get_music(update, context))
        
        try:
            context.user_data['music_task']
        except asyncio.CancelledError:
            pass  # Already handled above
        except Exception as e:
            await update.message.reply_text(f"Error: {str(e)}")


    
async def get_message(update:Update , context: ContextTypes.DEFAULT_TYPE):
    """ getting user messages and act proper behavier based on user input , 
    it can be music name , cancelation request , information request , or an invalid long messsage
    """
    music_name=update.message.text
    context.user_data['api_answer']=''

    # check if the music name is valid 
    if len(music_name)>50:
        await context.bot.send_message(chat_id=update.effective_chat.id , text=f"Invaid Song! please try again💗",reply_markup=ReplyKeyboardMarkup([["ℹ️ Help"]], resize_keyboard=True))
        return

    context.user_data['chat_id']=update.effective_chat.id
    # if any cancelation message apears , we cancel tasks . 
    if update.message.text == '🛑 Stop Recommending':
        # Cancel any ongoing AI processing
        if 'api_call' in context.user_data:
            context.user_data['api_call'].cancel()
            await asyncio.sleep(3)
            try:
                await context.user_data['api_call']
            except asyncio.CancelledError:
                print('api procees canceled :',context.user_data['api_call'].cancelled())
                await update.message.reply_text("Alright, No More recommends! 🦍",reply_markup=ReplyKeyboardMarkup([["ℹ️ Help"]], resize_keyboard=True))
            except Exception as e : 
                print('error came when we tried to process :',e)
                await update.message.reply_text("Alright, No More recommends! 🦍",reply_markup=ReplyKeyboardMarkup([["ℹ️ Help"]], resize_keyboard=True))
        # Cancel any ongoing music processing
        if 'music_task' in context.user_data:
            context.user_data['music_task'].cancel()
            try:
                await context.user_data['music_task']
            except asyncio.CancelledError:
                print('music procees canceled :',context.user_data['music_task'].cancelled())
                await update.message.reply_text("Alright, No More recommends! 🦍",reply_markup=ReplyKeyboardMarkup([["ℹ️ Help"]], resize_keyboard=True))
        return
    
    # show info to user 
    elif music_name == "ℹ️ Help":
        await context.bot.send_message(
                chat_id=update.effective_chat.id,
                text="Just send me the name of song and artist 🎙\nlike : instant crush by Daftpunk\n🎵 and I'll find similar tracks! 🦾",
                reply_markup=ReplyKeyboardRemove())
        return

    # start processing user's input      
    else: 
        await context.bot.send_message(chat_id=update.effective_chat.id , text=f" Hmm , Let me see what can i find ... 🗿\nBe patient im ( sooooo slow )🧠 🦥\n",reply_markup=ReplyKeyboardMarkup([["🛑 Stop Recommending"]], resize_keyboard=True))
        
        # make a api call task and passing the input to it 
        context.user_data['api_call'] = asyncio.create_task(
            api_call(music_name,update,context))
        
        try:
            context.user_data['api_call']
        except asyncio.CancelledError:
            pass  # Already handled above
        except Exception as e:
            await update.message.reply_text(f"Error: {str(e)}")
        
if __name__ == '__main__':
    application = ApplicationBuilder().token(os.getenv('TELEGRAM_BOT_TOKEN')).build()
    start_handler = CommandHandler('start', start)
    music_handler = MessageHandler(filters.TEXT & (~filters.COMMAND), get_message)

    application.add_handler(start_handler)
    application.add_handler(music_handler)
    
    application.run_polling()
