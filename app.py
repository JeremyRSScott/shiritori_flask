from flask import Flask, render_template, flash, request
from wtforms import Form, TextField, TextAreaField, validators, StringField, SubmitField
import re
import pandas as pd
import codecs
import csv
# App config.
DEBUG = True
app = Flask(__name__)
app.config.from_object(__name__)
app.config['SECRET_KEY'] = '7d441f27d441f27567d441f2b6176a'

class ReusableForm(Form):
    word = TextField('Word:', validators=[validators.required()])
    past_words =  TextField('Past Words:', validators=[])
    @app.route("/", methods=['GET', 'POST'])
    def hello():
        form = ReusableForm(request.form)
        df = load_jlpt_dataframe()
        df.columns=['name','hiragana','kanji']
        #print(df.head())
        with open('./assets/n3_csv_tanos.csv', newline='', encoding='utf-8') as f:
            reader = csv.reader(f)
            for row in reader:
                print(row)
        print(form.errors)
        if request.method == 'POST':
            word=request.form['word']
            past_words=''
            print(word)
        hiragana_full = r'[ぁ-ゟ]'
        if form.validate() and special_match(word):
            if(valid_word_played(word,request.form['past_words'])):
                if(request.form['past_words']==''):
                    past_words=request.form['word']
                else:
                    past_words=request.form['past_words'] + ',' + word
                print(word)

                # Save the comment here.
                form.past_words.data = past_words
                flash('Word Played ' + word)
            else:
                flash('Invalid Word Played')
        else:
            flash('A word must be played. It must be written in hirgana.')
        return render_template('game.html', form=form)

def load_jlpt_dataframe():
    df = pd.read_csv('./assets/n3_csv_tanos.csv',encoding='utf_8')
    return df

def special_match(strg, search=re.compile(r'[ぁ-ゟ]').search):
     return bool(search(strg))


def valid_word_played(played_word,past_words):
    print()
    if(len(past_words)==0):
        return True
    print("we good")
    past_word_arr = past_words.split(',')
    for item in past_word_arr:
        if(item==played_word):
            return False
    print("I'm not good")
    if(len(past_words)==1):
        return played_word[0]==past_words[0]
    else:
        return played_word[0]==past_words[-1:]


if __name__ == "__main__":
    app.run()
