# -*- coding: utf-8 -*-
from flask import Flask, render_template, flash, request
from wtforms import Form, TextField, TextAreaField, validators, StringField, SubmitField
import re
import pandas as pd
import codecs
import csv
from googletrans import Translator
import operator
import os.path
import random
import romkan

# App config.
DEBUG = True
TEMPLATE_DIR=os.path.abspath('./templates')
STATIC_DIR=os.path.abspath('./static')

application = Flask(__name__,template_folder=TEMPLATE_DIR, static_folder=STATIC_DIR)
#config.from_object(__name__)
application.config['SECRET_KEY'] = '7d441f27d441f27567d441f2b6176a'

class ReusableForm(Form):
    word = TextField('Word:', validators=[validators.required()])
    past_words =  TextField('Past Words:', validators=[])
    word_data = TextField('Word Data:',validators=[])

    @application.route("/", methods=['GET', 'POST'])
    def Play():
        form = ReusableForm(request.form)
        word=""
        word_data=""
        translator=Translator()
        translation=''
        if request.method == 'POST':
            translation = translator.translate(request.form['word'])
            past_words = request.form['past_words']
            word = request.form['word']
            word_data=request.form['word_data']
            past_words = ''

        if word_data=='':
            word_data='Welcome to the Shiritori Game! Please enter any valid word to get started. Good luck!'

        if form.validate() and special_match(word) and word[-1:]!='ん' and word!="" and valid_translate(word, translation.extra_data) and ',GIVEHINT' not in form.past_words.data and ',GIVEREFERENCES' not in form.past_words.data:
            if(valid_word_played(word,request.form['past_words'])):
                if(request.form['past_words']==''):
                    past_words=request.form['word']
                    word_data = request.form['word_data'] + "," + request.form['word']+"-"+parse_for_translation(translation.extra_data)
                else:
                    past_words=request.form['past_words'] + ',' + word
                    word_data =  request.form['word_data'] + ',' + word +'-'+parse_for_translation(translation.extra_data)
                response = ''
                trans=''
                new_word,trans = get_new_word(past_words, word[-1:])
                if new_word != '':
                    past_words = past_words + ',' + new_word
                    word_data = word_data + ',' + new_word + '-' + trans
                else:
                    word_data = word_data +',I couldn\'t find a word to play! Well done you have won!'
                form.past_words.data = past_words
                form.word.data=""
                form.word_data.data=word_data
            else:
                word_data+=form.word_data.data+",1. All words must start with the ending Kana of the previous word and be a single word. 2. Words cannot end in \'ん\'. 3. Words cannot be repeated. 4. Words cannot end in little kanas. 5. Words cannot translate to themselves in romaji(eg. names). 6. Words can only be written in hiragana."
                form.word_data.data=word_data
                form.word.data=""
        else:
            if(word[-1:]=='ん'):
                a=translator.translate(word)
                word_data+=form.word_data.data+","+word+"-"+parse_for_translation(translation.extra_data)+",Game over! You played a word ending in 'ん'. Thanks for playing!"
            elif word in form.past_words.data and word!='':
                word_data+=form.word_data.data+",Game over! You played a repeated word. Thanks for playing!"
            elif ',GIVEHINT' in word_data:
                if ',' not in request.form['past_words']:

                    word_data=word_data.replace('GIVEHINT','You have not even played a start word yet! Nice try :).')
                else:
                    wrd_arr = request.form['past_words'].split(',')
                    last_word = wrd_arr[len(wrd_arr)-1]
                    start_char = last_word[-1:]
                    wrd,trns = get_new_word(request.form['past_words'],start_char)

                    word_data=word_data.replace('GIVEHINT','A hint is a word that has the following English translation : '+trns)

            elif ',GIVEREFERENCES' in form.word_data.data:
                referenceString = GetReferences()
                word_data = form.word_data.data.replace('GIVEREFERENCES',referenceString)
            else:
                word_data+=form.word_data.data+",1. All words must start with the ending Kana of the previous word and be a single word. 2. Words cannot end in \'ん\'. 3. Words cannot be repeated. 4. Words cannot end in little kanas. 5. Words cannot translate to themselves in romaji(eg. names). 6. Words can only be written in hiragana."

            form.word_data.data=word_data
        form.word_data.data=word_data
        return render_template('game.html', form=form, pastwords="")

def GetReferences():
    return '<u>References </u>, 1. Murata&#44; M.&#44; & Shirado&#44; T. (2015). Statistical Investigation of a Japanese Word Chain Game. International Information Institute (Tokyo). Information&#44; 18(5(A))&#44; 1631.,2. locksleyu&#44; 2015&#44; Shiritori: Japanese Word Game&#44; http://selftaughtjapanese.com/2015/04/15/shiritori&#45;japanese&#45;word&#45;game/,3. Stack Overflow&#44; (2011)&#44; What issues lead people to use Japanese&#45;specific encodings rather than Unicode?&#44; https://softwareengineering.stackexchange.com/questions/82396/what&#45;issues&#45;lead&#45;people&#45;to&#45;use&#45;japanese&#45;specific&#45;encodings&#45;rather&#45;than&#45;unicode/82397,4. Tasarim&#44;Iphone6 Image&#44;http://www.adobewordpress.com/tasarim/images/iphone6.png'



def get_new_word(past_words,start_character):
    df = load_jlpt_dataframe()
    word = ''
    translated = ''
    rng = random.randrange(0,100)
    #if rng >=50:
    #    (word,translated) = n_bound_path_search(past_words,start_character,df)
    #else:
    #    (word,translated) = repeat_attack_search(past_words,start_character,df)
    if word == '':
            (word,translated) = get_any_word(past_words,start_character,df)
    return (word,translated)

def repeat_attack_search(past_words,start_character,df):
    character_count = {}
    past_word_arr = past_words.split(',')
    for wrd in past_word_arr:
        end_char = wrd[-1:]
        if end_char in character_count:
            character_count[end_char] += 1
        else:
            character_count[end_char] = 1
    try:
        max_key = max(character_count.keys(), key=character_count.get())
        print(max_key)
        for index,row in df.iterrows():
            if row['hiragana'][-1:] == max_key and row['hiragana'][0]==start_character and ','+row['hiragana']+',' not in past_words:
                return row['hiragana'],row['translation']
    except:
        a=''
    return '',''

def n_bound_path_search(past_words,start_character,df):
    word = ''
    word_n_count_path={}
    for index,row in df.iterrows():
        if ',' + row['hiragana'] + ',' in past_words or row['hiragana'][0] != start_character:
            continue
        else:
            word_n_count_path[row['hiragana']]=0
            for x,r in df.iterrows():
                if r['hiragana'][-1:]!='ん':
                    continue
                if r['hiragana'] not in past_words and r['hiragana'] != row['hiragana'] and r[0]==start_character :
                    word_n_count_path[row['hiragana']]+=1
    trans = ''
    try:
        word=max(word_n_count_path.keys(), key=word_n_count_path.get())
        for index,row in df.iterrows():
            if row['hiragana'] == word:
                trans = row['translation']
                break
        f=''
    except:
        word=''
    return word,trans

def get_any_word(past_words,start_character,df):
    print("fallback")
    word = ''
    trans = ''
    word_options = []
    i=0
    for index, row in df.iterrows():
        if row['hiragana'] not in past_words and row['hiragana'][0] == start_character and row['hiragana'][-1:]!='ん':
            word = row['hiragana']
            trans = row['translation']
            word_options.append((word,trans))
            i+=1
            if(i==5):
                break
    return random.choice(word_options)

def valid_translate(word_played, translation_data):
    word_played_romaji = romkan.to_roma(word_played)
    arrs = translation_data['translation']
    not_none = False
    for arr in arrs:
        if arr[0]!=None:
            not_none=True
            #if arr[0].lower()==word_played_romaji:
            #    return False
            if ' ' in arr[0].lower() and 'to　' not in arr[0].lower():
                return False
            elif '.' in arr[0].lower():
                return False
    return not_none

def parse_for_translation_exists(data):
    arrs = data['translation']
    for arr in arrs:
        if arr[0]!=None:
            return arr[0]

def parse_for_translation(data):
    arrs = data['translation']
    for arr in arrs:
        if arr[0]!=None:
            return arr[0]

def find_playable_endings(start_kana,arr):
    playable_kana_ends= []
    for item  in arr:
        if item[1][0]==start_kana and item[1][0] not in playable_kana_ends:
            playable_kana_ends += item[1][0]
    return playable_kana_ends

def find_most_n_word_ending(playable_kana_ends,arr,past_words):
    kvp = {}
    for end_kana in playable_kana_ends:
        for item in arr:
            if item[1][0]==end_kana:
                kvp[item[1]]=0
                for x in arr:
                    if x[1][-1:] == 'ん' and item[1][-1:]==x[1][0] and x[1] not in past_words:
                        kvp[item[1]]+=1
    max_word = max(kvp.items(), key=operator.itemgetter(1))[0]
    return max_word

def load_jlpt_dataframe():
    df = pd.read_csv('./assets/jlpt_words.csv',encoding='utf_8')
    df.columns=['index','hiragana','romaji','kanji','translation','example_usage']
    return df

def special_match(strg, search=re.compile(r'[ぁ-ゟあ]').search):
     return bool(search(strg))

def format_arr(arr):
    new_arr = []
    for item in arr:
        row_arr = []
        split = item.split(',')
        for x in split:
            row_arr+=split
        new_arr+=[row_arr]
    return new_arr

def valid_word_played(played_word,past_words):
    if(len(past_words)==0):
        return True
    past_word_arr = past_words.split(',')
    for item in past_word_arr:
        if(item==played_word):
            return False
    if(len(past_words)==1):
        return played_word[0]==past_words[0]
    else:
        return played_word[0]==past_words[-1:]


if __name__ == "__main__":
    application.run()
