#imports
import audiomath; audiomath.RequireAudiomathVersion( '1.12.0' )
import speech_recognition as sr
from duck_typed_microphone import DuckTypedMicrophone
from fuzzywuzzy import fuzz, process #'fuzzy' matching
from guizero import *
from json import load
from gspread import service_account
from random import choice,randint,shuffle
from pytube import *
# from moviepy.editor import *
import os
import smtplib
import hashlib#importing module
import ast
from user_profileClass import User

#accessing local word bank as refrence data
#creating globals
with open("words_dictionary.json") as f:
    database = load(f)
f.close()

#accessing online bsl database
gc = service_account(filename="credentials.json")
bsl_worksheet = sh.sheet1#selects the first sheet of the documment
total_vids = bsl_worksheet.get_all_records()

#accessing online user database
#this is the key for the google docs. this can be found in the URL after the /d/
user_worksheet = sh2.sheet1#selects the first sheet of the documment
total_users = user_worksheet.get_all_records()

#obtaining email and password from local environment variables
EMAIL_ADDRESS = None
EMAIL_PASSWORD = None

#globals
top_20_list = []
letter_list = []
consolidation_list = []
tailored_list = []
template_list = []
search_output_file_names = []
consolidation_list = []
alphabet_list = ["a","b","c","d","e","f","g","h","i","j","k","l",
"m","n","o","p","q","r","s","t","u","v","w","x","y","z"]
global signed_in
signed_in = False
predict_desc = None
sign_up_code = 0
user_object = None

#functions
def set_user_counter():
    """method that sets the user counter as the most recent user number.
    This function should be called each time the program is run so that 
    the user number can be set to the correct number."""
    User.user_counter = total_users[-1]["User number"]

def mic_input():
    """function called when mic button is pressed.
    allows the user to use the microphone for audio input to text
    uses local function to insert result into text box"""
    microphone_input = ""
    r = sr.Recognizer()
    with DuckTypedMicrophone() as source:#uses local module as a microphone inputter
        r.adjust_for_ambient_noise(source)
        audio = r.listen(source)#converts the input from the microphone to audio data object
    try:
        #performs a speech recognition on an audio data instance using Google Speech Recognition API
        microphone_input = ('%s' % r.recognize_google(audio))
    except:
        #excepts unknown input that cannot be translated or any other errors such as no network connection
        microphone_input = ("sorry, unable to translate audio")
    if 0: # plot and/or play back captured audio
        s = audiomath.Sound(audio.get_wav_data(), fs=audio.sample_rate, nChannels=1)
        s.Play()
        s.Plot()
    search_engine.value = microphone_input

def search_conditioning(user_input):
    """function gets rid of any special characters or numbers but keeps spaces.
    returns the conditioned string"""
    new_string = ""
    for i in range(len(user_input)):
        #loops through the string and checks if every character is a letter
        if user_input[i] == " ":#keeps the spaces
            new_string += user_input[i]
        elif user_input[i].isalpha():
            new_string += user_input[i].lower()
            #only adds the letters to the final string
    return new_string

def fluffy_search(database,user_input,desired_percent):
    single_word_list = []#this list stores potential phrases for the user input
    for phrase in database:#loops through the entire database
        if phrase[0] == user_input[0]:
            options_list = []#temp list to store each potential phrase
            percent_acc = fuzz.ratio(user_input,phrase)
            #uses fuzz.ratio to find how similar the input is to words in the database
            if percent_acc > desired_percent:#if the word is relatively accurate
                options_list.append(phrase)#adds the phrase to the temp list 
                options_list.append(percent_acc)#adds the level of accuracy to the temp list
                for i in range(len(single_word_list)):#loops through the entire selection of possibilities
                    phrase_percent = int(single_word_list[i][1])
                    if percent_acc>=phrase_percent:
                        single_word_list.insert(i,options_list)
                        #inserts the temp list with the newest phrase so that the final list is sorted 
                        break#breaks out of the loop
                    elif (i+1) == len(single_word_list):
                        single_word_list.insert(i+1,options_list)
                        #if the phrase is the least accurate it is inserted to the back of the list
                        break#breaks out of the loop
                if len(single_word_list) == 0:#if there are no values in the list
                    single_word_list.append(options_list)
    return single_word_list

def searching_database(user_input,output_text):
    """takes user input as an attribute and searches through the database for it.
    this includes a fluffy search which outputs the most accurate word it can find in the database.
    this function also updates the top 20 list"""
    user_input_list = user_input.split()
    output_string = ""
    temp_list = []
    total_list = []
    my_gui_string = ""
    for i in range(len(user_input_list)):#iterates through each inputted word       
        single_word_list = fluffy_search(database,user_input_list[i],80)#creates a list of possible phrases
        total_list.append(single_word_list)#appends all possible phrases for each inputted word to total list
        if len(single_word_list) != 0:#if there were no found possibilities
            my_gui_string = top_20_adjust(top_20_list,total_list[i][0][0])
            #adds the searched phrase to the top 20 list and returns the new top 20 list to output
            output_string += total_list[i][0][0] + " " #adds new value to output to be printed
    
    if output_string == "":#if nothing was added to the string - if no words found in database
        output_text.value = "Sorry. That couldn't be found, please try again" 
        signing_page_button.visible = False
    else:
        output_string = output_string.strip()#gets rid of any possible spaces on the ends
        correction = False#used to check if input needed to be corrected
        for word_list in total_list:
            if word_list[0][1] != 100:#if the accuracy value was not 100
                correction = True#phrase was corrected
        #different output message shown telling user if the phrase was corrected or not
        if correction == True:
            output_text.value = "Showing most similar phrases: " + str(output_string)
        else:
            output_text.value = "Found it: " + str(output_string)
        signing_page_button.visible = True
        #presents the validated output to the user
    top_20_output_text.value = my_gui_string  

def search_phrase():
    """function is called when enter button is pressed.
    starts by conditioning string and inserting validated string in the text box"""
    user_input = search_conditioning(search_engine.value)
    search_engine.value = user_input#inserts validated string in text box
    searching_database(user_input,output_text)#checks the validated string against database   

def top_20_adjust(top_20_list,new_value):
    """function adds the new value to the front of the list.
    if the list is bigger than 20 value is removes one from the back
    and adds the new one to the front"""
    if len(top_20_list) == 20:
        top_20_list.pop(-1)#removes value from the back of the list
        top_20_list.insert(0,new_value)#adds to front
    else:
        top_20_list.insert(0,new_value)#adds to front
    output_string = top_20_format(top_20_list) 
    return output_string

def top_20_format(my_list):
    """function formats the lists so that they can be more easily displayed.
    creates a 2d list with up to 4 values in each of the inner lists."""
    list_1 = []
    for i in range(len(my_list)):
        if i %4 == 0:#if the index of the list is a multiple of 4 - this includes 0
            list_1.append([])#creates new inner list
            list_1[-1].append(my_list[i])#adds value to the back-most inner list
        else:
            list_1[-1].append(my_list[i])#adds value to the back-most inner list
    output_string = top_20_output(list_1)
    return output_string

def top_20_output(my_list):
    """function uses the formatted lists to display the values in 
    4 colums with up to 20 values"""
    output_string = ""
    short_list = []
    iteration = 5
    if len(my_list)<iteration:#output should have 5 rows or less
        iteration = len(my_list)
    for i in range(iteration):
        short_list.append(my_list[i])#takes the first 5 "rows" of data
    col_width = max(len(word) for row in short_list for word in row)+2 
    # calculates the necessary spacing between each columns for neat formations
    counter = 0
    for row in short_list:
        if counter<5:#second level of validation to make sure no more than 5 rows
            output_string += ("".join(word.ljust(col_width) for word in row) + "\n")
            #creates a string with all values in ordered fashion
        counter+=1
    return output_string

def alphabet_display(letter):#beginning letter passed through
    """function takes a letter and creates a list of all the phrases beginning 
    with that letter from the database"""
    del letter_list[:]#list is cleared before initiation so values are not added to a full list
    counter = 0
    for word in total_vids:
        if word["Phrase"][0].lower() == letter:#if beginning letters match
            letter_list.append(word["Phrase"])#adds it to the list
    output_string = top_20_format(letter_list)#formats the list for a top 20
    alphabet_output.value = output_string
    return letter_list

def alphabet_iteration():
    """function allows the user to iterate through the values from the letter_list
    and shows the next 20 values"""
    if len(letter_list) == 0:
        #if there are no values in the letter_list
        #function will do nothing
        return
    else:
        current_letter = alphabet.value
        if len(letter_list)<=20:#if no further iteration can happen
            alphabet_display(current_letter)#redo the list
        else:
            del letter_list[:20]
            output_string = top_20_format(letter_list)#formats the list for a top 20
            alphabet_output.value = output_string#outputs to GUI
        return letter_list

def create_url_list(user_string):
    found_values = []#list of phrases that are in input
    user_input_list = user_string.split()
    for i in range(len(user_input_list)):
        #creates 2d list of input [user word,index of given phrase in found_values]
        user_input_list[i] = [user_input_list[i]]
        user_input_list[i].append(None)

    for value in total_vids:#loops through all phrases
        db_phrase = value["Phrase"].lower()#uses lowercase phrases
        if db_phrase in user_string:#if phrase present in input
            found_values.append(value["Phrase"])#appends formatted phrase to list
            for i in range(len(user_input_list)):#loops through each word of user input
                if db_phrase.split()[0] == user_input_list[i][0]:#lines up phrase and user input
                    for j in range(len(db_phrase.split())):#loops through length of phrase
                        if user_input_list[i+j][1] == None:#if there isnt anything found for a phrase
                            user_input_list[i+j][1] = len(found_values)-1
                            #current phrase set as value via pointer
                        elif len(db_phrase.split()) > len(found_values[user_input_list[i+j][1]]):
                            #if current phrase is bigger than previous phrase 
                            user_input_list[i+j][1] = len(found_values)-1
                            #current phrase set at value via pointer

    for i in range(len(user_input_list)):#iterating through user input
        if user_input_list[i][1] == None:#find word that has no signings
            temp_list = []
            for j in range(len(user_input_list[i][0])):#loops through length of word
                for k in range(len(found_values)):#loops through the found values
                    if user_input_list[i][0][j] == found_values[k].lower():
                        #if current letter is the letter in found values
                        temp_list.append(k)#appends index of letter to temp list
                        break
            user_input_list[i][1] = temp_list
            #temp list is used in place where other words have a single phrase
    return user_input_list,found_values

def gif_setup():
    """this function finds the signings of the specific phrases in online database"""
    #obtains corrected user input
    corrected_input = ""
    for i in range(len(output_text.value)):
        if output_text.value[i] == ":":
            corrected_input = output_text.value[i+2:]
            break
    #sets intro text value
    search_result_user_input.value = "Searching for: " + corrected_input
    clear_search_page()
    del search_output_file_names[:]#clears the global list 
    user_input_list,found_values = create_url_list(corrected_input.lower())
    #obtains the total phrases found in the input and a 2d list containing
    #each word in the input and a pointer to a value in the found_values list
    temp_list = []
    counter = 0
    while counter < len(user_input_list):
        #this loops round the 2d list and abstracts all of the phrase descriptions
        #by looking at each of the indexes in found_values list
        if type(user_input_list[counter][1]) is list:
            for j in range(len(user_input_list[counter][1])):
                search_output_file_names.append(found_values[user_input_list[counter][1][j]])
            counter+=1
        else:
            search_output_file_names.append(found_values[user_input_list[counter][1]])
            counter+=len(found_values[user_input_list[counter][1]].split())
    iterate_search_result()

def iterate_search_result():
    """Outputs each signing and iterates to the next signing phrase in the list when the button pressed.
    Downloads the next signing video phrase and converts it into .gif.
    The iteration button only appears if there is more than one phrase.
    Also updates the text at the top indicating what is currently being displayed."""
    search_result_gif_output.value = None
    #shows the iterate button if there are more than one phrases
    if len(search_output_file_names)>1:
        search_result_next_button.show()
    else:
        search_result_next_button.hide()
    try:
        #presents description of the current phrase being shown
        search_resut_current_output.value = "Currently showing: "+str(search_output_file_names[0])
        if not os.path.exists(search_output_file_names[0]+".gif"):
            #if video needs to be    
            for value in total_vids:#obtains correct URL
                if search_output_file_names[0] == value["Phrase"]:
                    output_url = value["URL"]
                    break
            ytd = YouTube(output_url).streams.first().download(filename=search_output_file_names[0])
            print("Video downloaded to local directory")
            file_name = search_output_file_names[0] + ".mp4"
            clip = (VideoFileClip(file_name))#creates clip instance
            file_name = file_name.replace(".mp4",".gif")#changes the file type on string
            clip.write_gif(file_name)#converts .mp4 video to .gif
            
            search_result_gif_output.image = file_name#outputs first value in list
            del search_output_file_names[0]#gets rid of the first value in list
        else:
            
            file_name = search_output_file_names[0]+".gif"
            search_result_gif_output.image = file_name#outputs first value in list
            del search_output_file_names[0]#gets rid of the first value in list        
    except:
        pass

def creating_user_object(name,username,password,email,user_number=None,
date_joined=None,started_TL=None,learning_path=None,total_right=None,total_wrong=None):
    """creates and returns a user object using values from signup page"""
    global user_object
    user_object = User(name,username,password,email,user_number,date_joined,started_TL,
    learning_path,total_right,total_wrong)#creates user object

def add_user_to_database(user_object):
    """function abstracts all of the data from the user object and appends the
    data to the database. This data is added to the online database"""
    temp_list = []
    #values are added to an array
    temp_list.append(user_object.user_number)
    temp_list.append(user_object.name)
    temp_list.append(user_object.username)
    temp_list.append(user_object.password)
    temp_list.append(user_object.email)
    temp_list.append(user_object.date_joined)
    temp_list.append(user_object.started_TL)
    temp_list.append(str(user_object.learning_path))
    #user's consolidation data saved as a list within a string which is then extracted on retrieval
    #array added to the online user database in a row
    user_worksheet.append_row(temp_list)

def updating_row():
    global user_object
    temp_list = []
    #values are added to an array
    temp_list.append(user_object.user_number)
    temp_list.append(user_object.name)
    temp_list.append(user_object.username)
    temp_list.append(user_object.password)
    temp_list.append(user_object.email)
    temp_list.append(user_object.date_joined)
    temp_list.append(user_object.started_TL)
    temp_list.append(str(user_object.learning_path))
    temp_list.append(user_object.total_right)
    temp_list.append(user_object.total_wrong)
    #user's consolidation data saved as a list within a string which is then extracted on retrieval
    #array added to the online user database in a row
    row_number = user_object.user_number + 1
    user_worksheet.delete_row(row_number)
    user_worksheet.insert_row(temp_list,row_number)

def existing_user_login(username,password):
    """Creates a user object from user database.
    Correct details are assured as username is unique(primary key)"""
    global total_users
    total_users = user_worksheet.get_all_records()
    #refreshes the local database from the online database
    current_user = False
    for profile in total_users:
        if profile["Username"] == username:#looks for user profile
            init_password = str.encode(password)
            #encodes the password in the same way so that they match if inputs match
            hashed_password = hashlib.sha224(init_password).hexdigest().strip("0")
            if profile["Password"] == hashed_password:#if password is correct
                #obtains all the user information
                user_number = profile["User number"]
                name = profile["Name"]
                username = profile["Username"]
                password = profile["Password"]
                email = profile["Email"]
                date_joined = profile["Date joined"]
                started_TL = profile["Started tailored learning"]
                learning_path = profile["Learning path"]
                total_right = profile["Total right"]
                total_wrong = profile["Total wrong"]
                creating_user_object(name,username,password,email,
                user_number,date_joined,started_TL,learning_path,
                total_right,total_wrong)
                #creates a user object
                current_user = True
    return current_user

def create_random_practice_list():
    """creating a list of 10 random phrases with URL"""
    my_list = []
    for i in range(10):
        random_phrase = choice(total_vids)
        if random_phrase not in my_list:
            my_list.append(random_phrase)
    for value in total_vids:
        if value["Phrase"] == "Telephone":
            my_list.append(value)
    return my_list

def starting_consolidation():
    begin_text.value = "Beginning Random Consolidation"
    begin_practise_button.hide()
    consolidation_finish_text.hide()
    global consolidation_list# uses global list so that it can be accessed during iteration
    consolidation_list = create_random_practice_list()#creates a random list of 20 phrases
    iterate_consolidation_output()#first iteration initiallising all of the functionality

def iterate_consolidation_output():
    consolidation_gif_output.image = None
    consolidation_phrase_text.hide()
    consolidation_reveal_desc.hide()
    if len(consolidation_list)>1:
        consolidation_iterate_button.show()
        begin_practise_button.show()
    else:
        consolidation_iterate_button.hide()
        consolidation_finish_text.show()
    try:
        if not os.path.exists(consolidation_list[0]["Phrase"]+".gif"):
            #if video needs to be downloaded
            output_url = consolidation_list[0]["URL"]
            ytd = YouTube(output_url).streams.first().download(filename=consolidation_list[0]["Phrase"])
            print("Video downloaded to local directory")
            file_name = consolidation_list[0]["Phrase"] + ".mp4"
            clip = (VideoFileClip(file_name))#creates clip instance
            file_name = file_name.replace(".mp4",".gif")#changes the file type on string
            clip.write_gif(file_name)#converts .mp4 video to .gif
            consolidation_gif_output.image = file_name#outputs first value in list
            consolidation_gif_output.show()
            consolidation_reveal_desc.show()
            consolidation_phrase_text.value = "The Phrase is: " + consolidation_list[0]["Phrase"]
            del consolidation_list[0]#gets rid of the first value in list
        else:
            file_name = consolidation_list[0]["Phrase"]+".gif"
            consolidation_gif_output.image = file_name#outputs first value in list
            consolidation_gif_output.show()
            consolidation_reveal_desc.show()
            consolidation_phrase_text.value = "The Phrase is: " + consolidation_list[0]["Phrase"]
            del consolidation_list[0]#gets rid of the first value in list        
    except:
        pass

def show_consolidation_phrase():
    consolidation_phrase_text.show()

def send_confirmation_email():
    """function sends an email to the user containing a confirmation code"""
    sign_up_code = randint(100000,999999)#generates a random 6-digit code as the validation code
    #obtains the user's username to be used as refrence in the email
    username = signup_username_input.value
    email = signup_email_input.value
    password = signup_password_input.value
    name = signup_name_input.value
    passed = False
    with smtplib.SMTP("smtp.outlook.com",587) as smtp:
        #initialising the connection
        smtp.ehlo()
        smtp.starttls()
        smtp.ehlo()        
        smtp.login(EMAIL_ADDRESS,EMAIL_PASSWORD)
        #creates the message in the email
        subject = "Sign Language Translator Sign Up"
        body = "This is a confirmation email for an account made for Sign Language Translator.\n"
        body+="Username: " + str(username) + "\n\n"
        body += "Please enter the following code to verify your account: " + str(sign_up_code)
        msg = f"Subject: {subject}\n\n{body}"#formats the message
        try:
            if len(name)>0 and len(password)>0 and len(username)> 0:
                smtp.sendmail(EMAIL_ADDRESS,email,msg)#sends message from admin email to user
                passed = True
        except:
            pass
    return sign_up_code,passed

def confirming_sign_up_code():
    """procedure checks whether the user has entered the correct confirmation code"""
    try:
        user_input = int(confirmation_code_box.value)
        sign_up_code = int(confirmation_holder.value)
        if user_input == sign_up_code:
            confirmation_output_text.value = "Code confirmed."
            confirmation_continue_button.show()
            confirmation_enter_button.hide()
        else:
            #if the code wasn't correct
            confirmation_output_text.value = "Incorrect code. Please recheck your email"
    except:
        #if the input contains something that isnt a number
        confirmation_output_text.value = "Please enter 6-digit code"

def sign_out():
    global user_object
    global signed_in
    updating_row()
    signed_in = False
    del user_object
    user_object = None
    home_loggedin_page.hide()
    home_page.show()

def tailored_predict_desc():
    """This function is used when the user wants to see the actions/.gif
    and wants to guess the phrase/description.
    This functtion initialises this specific tailored learning"""
    tailored_phrase_then_desc.hide()
    tailored_desc_then_phrase.hide()
    tailored_consolidation_options.hide()
    global predict_desc
    predict_desc = True
    #this dictates to other functions which type of tailred learning is being done
    global tailored_list
    del tailored_list[:]#this is the list for practised phrases (queue)
    global template_list
    del template_list[:]#this is a template used to set the queue of phrases
    template_list = create_template_list()
    for value in template_list:
        #the queue of phrases with tailored repeats is made from the template 
        #phrases that the user is less confident in have more repeats
        for i in range(5-int(value["Confidence"])):
            tailored_list.append(value)
    shuffle(tailored_list)#queue is shuffled
    tailored_consolidation()#starting the consolidation

def tailored_predict_phrase():
    """This function is used when the user wants to see the phrase/
    description and wants to guess the actions/.gif"""
    tailored_phrase_then_desc.hide()
    tailored_desc_then_phrase.hide()
    tailored_consolidation_options.hide()
    global predict_desc
    predict_desc = False
    #this dictates to other functions which type of tailred learning is being done
    global tailored_list
    del tailored_list[:]#this is the list for practised phrases (queue)
    global template_list
    del template_list[:]#this is a template used to set the queue of phrases
    template_list = create_template_list()
    for value in template_list:
        #the queue of phrases with tailored repeats is made from the template 
        #phrases that the user is less confident in have more repeats
        for i in range(5-int(value["Confidence"])):
            tailored_list.append(value)
    shuffle(tailored_list)#queue is shuffled
    tailored_consolidation()#starting the consolidation

def create_template_list():
    global user_object
    #checks whether the user has done tailored learning
    #if yes the user already has a list of phrases to use
    if user_object.started_TL == "Yes":
        temp_list = []
        for practised_phrase in user_object.learning_path:
            #learning path is the attribute of the obeject 
            # that contains the user history
            if practised_phrase["Confidence"] != 5:
                #the number 5 dictates the number of points needed
                #to achieve "mastery"
                temp_list.append(practised_phrase)
                #only non mastered phrases are added 
                #to be learnt in continuation      
    else:
        #user needs a new set of phrases to learn
        temp_list = create_random_practice_list()
        for value in temp_list:
            value.update({"Confidence":0})
        user_object.started_TL = "Yes"
        user_object.learning_path = []
        for i in range(len(temp_list)):
            user_object.learning_path.append(temp_list[i])
    return temp_list

def tailored_consolidation():
    #presets all of the GUI objects
    tailored_gif_output.image = None
    tailored_gif_output.hide()
    tailored_phrase_text.hide()
    tailored_reveal.hide()
    tailored_iteration_button.hide()
    tailored_feedback_text.hide()
    tailored_correct_button.hide()
    tailored_incorrect_button.hide()
    global predict_desc
    try:
        if not os.path.exists(tailored_list[0]["Phrase"]+".gif"):
            #if the video is not already installed in the local directory 
            output_url = tailored_list[0]["URL"]
            ytd = YouTube(output_url).streams.first().download(filename=tailored_list[0]["Phrase"])
            print("Video downloaded to local directory")
            file_name = tailored_list[0]["Phrase"] + ".mp4"
            clip = (VideoFileClip(file_name))#creates clip instance
            file_name = file_name.replace(".mp4",".gif")#changes the file type on string
            clip.write_gif(file_name)#converts .mp4 video to .gif

            tailored_gif_output.image = file_name#outputs first value in list
            tailored_reveal.show()#shows the button to reveal the phrase/gif depending
            tailored_phrase_text.value = "The Phrase is: " + tailored_list[0]["Phrase"]
            if predict_desc:
                tailored_gif_output.show()#shows the gif
            else:
                tailored_phrase_text.show()#shows the description
        else:
            file_name = tailored_list[0]["Phrase"]+".gif"
            tailored_gif_output.image = file_name#outputs first value in list
            tailored_reveal.show()#shows the button to reveal the phrase/gif depending
            tailored_phrase_text.value = "The Phrase is: " + tailored_list[0]["Phrase"]
            if predict_desc:
                tailored_gif_output.show() #shows the .gif  
            else:
                tailored_phrase_text.show()#shows the description 
    except:
        pass    

def show_tailored_phrase():
    global predict_desc
    if predict_desc:
        tailored_phrase_text.show()
    else:
        tailored_gif_output.show()
    tailored_feedback_text.show()
    tailored_correct_button.show()
    tailored_incorrect_button.show()

def correct_tailored_consolidation():
    global template_list
    global tailored_list
    global user_object
    user_object.total_right += 1
    for i in range(len(template_list)):
        if template_list[i]["Phrase"] == tailored_list[0]["Phrase"]:
            template_list[i]["Confidence"] += 1
            #increases confidence in template list for specific phrase that user got right
            if int(template_list[i]["Confidence"]) == 5:#if user has "mastered" the phrase
                removed = False
                while not removed:
                    #loops through and removes all other of that phrase from tailored_list (queue)
                    edited = False
                    for j in range(len(tailored_list)):
                        if tailored_list[j]["Phrase"] == template_list[i]["Phrase"]:
                            edited=True
                            del tailored_list[j]
                            break
                    if not edited:
                        removed = True
                temp_var = template_list[i]
                user_object.learning_path.append(temp_var)
                #appends mastered value to the user object to be stored
                del template_list[i]
                #deletes the value from the template list
                
                for k in range(len(total_vids)):#loops through the the video database
                    random_phrase = total_vids[k]
                    for complete_phrase in user_object.learning_path:
                        #loops through the users consolidation history
                        if complete_phrase["Phrase"] == random_phrase["Phrase"]:
                            #checks if the phrases are the same
                            if k == len(total_vids)-1:#if its the last phrase
                                random_phrase = choice(total_vids)
                                #uses a random phrase for the next phrase
                        else:
                            break #uses the next available phrase
                    break
                random_phrase.update({"Confidence":0})
                #inserts confidence key:value into the dictionary
                template_list.append(random_phrase)
                #adds the new phrase to be learnt to the template list
                user_object.learning_path.append(random_phrase)
                #adds the new phrase to be learnt to the user's history 
                for i in range(5):
                    tailored_list.append(random_phrase)
                    #adds the new phrase to the practise list - to be practised 5 times
                shuffle(tailored_list)
                #shuffles the list so the same phrases aren't adjacent
            else:  
                del tailored_list[0]
                #deletes the most phrase that was answered right from the queue
            break
    tailored_feedback_text.show()
    tailored_correct_button.hide()
    tailored_incorrect_button.hide()
    tailored_feedback_text.hide()
    tailored_iteration_button.show()
    tailored_reveal.hide()

def incorrect_tailored_consolidation():
    global template_list
    global tailored_list
    global user_object
    user_object.total_wrong += 1
    for value in template_list:
        if value["Phrase"] == tailored_list[0]["Phrase"] and value["Confidence"]!=0:
            #finds phrase in template list and only adjusts if confidence >0
            value["Confidence"]-= 1#adjusts the confidence value for the given phrase
            tailored_list.append(value)
            #adds same phrase to the back twice 
            #due to decrease in confidence
            break
    del tailored_list[0]#allows iteration to next value
    tailored_list.append(value)
    shuffle(tailored_list)
    tailored_feedback_text.show()
    tailored_correct_button.hide()
    tailored_incorrect_button.hide()
    tailored_feedback_text.hide()
    tailored_iteration_button.show()
    tailored_reveal.hide()

def change_password():
    global total_users
    global user_object
    total_users = user_worksheet.get_all_records()
    password = settings_old_password_input.value
    init_password = str.encode(password)
    hashed_password = hashlib.sha224(init_password).hexdigest().strip("0")
    both_equal = False
    for i in range(len(total_users)):
        if total_users[i]["Password"] == hashed_password:
            if settings_new_password_input.value == settings_confirm_password_input.value:
                both_equal = True
                new_password = str.encode(settings_new_password_input.value)
                hashed_new_password = hashlib.sha224(new_password).hexdigest().strip("0")
                user_object.password = hashed_new_password
                updating_row()
                settings_old_password_input.value = ""
                settings_new_password_input.value = ""
                settings_confirm_password_input.value = ""
                settings_password_error.value = "Password changed successfully"
        elif i == len(total_users)-1:
            settings_password_error.value = "Please enter the correct original password"
    if not both_equal:
        settings_password_error.value = "Please enter the same new password"

#GUI page switching
def quit_program():
    app.destroy()

def home_page_login():
    """This function allows the user to log in"""
    username = home_page_username_input.value
    password = home_page_password_input.value
    global signed_in
    if not signed_in:
        signed_in = existing_user_login(username,password)
    if signed_in:
        home_page_to_loggedin()
    else:
        #if it cannot sign in it will display an error message to the user
        home_page_login_error.show()

def home_page_to_loggedin():
    """This function switches the page from the home page
    to the logged in page."""
    home_page.hide()
    home_loggedin_page.show()

def loggedin_to_search():
    """This function switches the page from the logged
    in page to the search page"""
    home_loggedin_page.hide()
    search_page.show()

def loggedin_to_settings():
    """This function switches the page from the logged in
    page to the settings page"""
    home_loggedin_page.hide()
    settings_page.show()
    adjusted_name = user_object.name.title()
    settings_name.value = "Name: " + str(adjusted_name)
    settings_username.value = "Username: " + str(user_object.username)
    settings_date_joined.value = "Date joined: " + str(user_object.date_joined)
    settings_email.value = "Email: " + str(user_object.email)
    settings_total_right.value = "Total right answers: " + str(user_object.total_right)
    settings_total_wrong.value = "Total wrong answers: " + str(user_object.total_wrong)

def settings_to_loggedin():
    """This function switches the page from the settings page back to the logged in page """
    settings_page.hide()
    home_loggedin_page.show()
    settings_old_password_input.value = ""
    settings_new_password_input.value = ""
    settings_confirm_password_input.value = ""
    settings_password_error.value = ""

def clear_search_page():
    """This function clears the search page"""
    del letter_list[:]
    del letter_list[:]
    search_engine.value = ""
    alphabet_output.value = ""
    output_text.value = ""

def clear_home_page():
    """This function clears the home page"""
    home_page_username_input.value = ""
    home_page_password_input.value = ""
    home_page_login_error.hide()

def clear_signup_page():
    """This function clears the signup page"""
    signup_name_input.value = ""
    signup_username_input.value = ""
    signup_password_input.value = ""
    signup_email_input.value = ""

def clear_confirmation_page():
    """This function clears the confirmation page"""
    confirmation_code_box.value = ""

def clear_tailored_learning():
    """This function resets and clears the tailored learning page"""
    tailored_phrase_text.hide()
    tailored_gif_output.hide()
    tailored_iteration_button.hide()
    tailored_reveal.hide()
    tailored_feedback_text.hide()
    tailored_correct_button.hide()
    tailored_incorrect_button.hide()
    tailored_phrase_then_desc.show()
    tailored_desc_then_phrase.show()
    tailored_consolidation_options.show()

def clear_consolidation():
    """This function clears and resets the consolidation page"""
    del consolidation_list[:]
    consolidation_phrase_text.hide()
    consolidation_finish_text.hide()
    consolidation_reveal_desc.hide()
    consolidation_iterate_button.hide()
    consolidation_gif_output.hide()

def home_to_search():
    """This function switches the page from the home page
    to the search page"""
    home_page.hide()
    search_page.show()
    clear_home_page()

def search_to_home():
    """This function switches the page from the search page
    to the home page"""
    global signed_in
    if signed_in:
        search_page.hide()
        home_loggedin_page.show()
        clear_search_page()
    else:
        search_page.hide()
        home_page.show()
        clear_search_page()

def home_to_signup():
    """This function switches the page from the home page
    to the signup page"""
    home_page.hide()
    sign_up_page.show()
    clear_home_page()

def signup_to_home():
    """This function switches the page from the signup page
    to the home page"""
    sign_up_page.hide()
    home_page.show()
    clear_signup_page()

def home_to_consolidation():
    """This function switches the page from the home page
    to the consolidation page"""
    home_page.hide()
    consolidation_page.show()

def consolidation_to_home():
    """This function switches the page from the consolidation page
    to the home page"""
    consolidation_page.hide()
    home_page.show()
    clear_consolidation()

def loggedin_to_tailored_consolidation():
    """This function switches the page from the logged in page
    to the tailored consolidation page"""
    home_loggedin_page.hide()
    tailored_consolidation_page.show()

def tailored_consolidation_to_loggedin():
    """This function switches the page from the tailored consolidation page
    to the logged in page. Updates learning path stored in user object"""
    tailored_consolidation_page.hide()
    home_loggedin_page.show()
    clear_tailored_learning()
    global template_list
    for i in range(len(user_object.learning_path)):
        for j in range(len(template_list)):
            if user_object.learning_path[i]["Phrase"] == template_list[j]["Phrase"]:
                user_object.learning_path[i]["Confidence"] = template_list[j]["Confidence"]
                break

def search_result_to_search():
    """This function switches the page from the search result page
    back to the search page"""
    search_result_page.hide()
    search_page.show()
    search_result_gif_output.value = None
    
def search_to_search_result():
    """This function switches the page from the search page
    to the search result page"""
    search_page.hide()
    search_result_page.show()
    signing_page_button.visible = False
    gif_setup()

def sign_up_to_confirmation():
    """This function switches the page from the signup page
    to the confirmation page"""
    sign_up_code,passed = send_confirmation_email()
    if not passed:
        signup_output_text.value = "Please enter valid values into each box"
    username = signup_username_input.value
    email = signup_email_input.value
    for profile in total_users:
        if profile["Username"] == username:
            passed = False
            signup_output_text.value = "This username has been taken. Please try another"
        elif profile["Email"] == email:
            passed = False
            signup_output_text.value = "There is already an account for this email. Please try a different email or login"
    if passed:#passed variable is true if the email was sent
        sign_up_page.hide()
        confirmation_holder.value = sign_up_code
        confirmation_page.show()

def confiramtion_to_sign_up():
    """This function switches the page from the confirmation page
    to the signup page"""
    sign_up_page.show()
    confirmation_page.hide()
    confirmation_output_text.value = ""

def confirmation_to_home():
    """This function switches the page from the confirmation page
    back to the home page"""
    name = signup_name_input.value
    username = signup_username_input.value
    password = signup_password_input.value
    init_password = str.encode(password)
    hashed_password = hashlib.sha224(init_password).hexdigest().strip("0")
    email = signup_email_input.value
    creating_user_object(name,username,hashed_password,email)
    add_user_to_database(user_object)
    signed_in = True
    confirmation_page.hide()
    home_page.show()
    clear_confirmation_page()
    clear_signup_page()
    home_page_to_loggedin()

def print_user_object():
    print(signed_in)
    print(user_object)
    print()


set_user_counter()
#creating GUI
app = App(title="Zain Altaf 4132 main",width=1400,height=700,layout="grid",bg=(99,207,237))

#home page objects
home_page = Box(app,layout="grid",align="left",grid=[0,0],visible=True)
home_page_welcome_text = Text(home_page,text="Welcome to the sign language translator",grid=[0,0],color="white",align="left",size=20)
home_page_login_text = Text(home_page,text="Login Here: ",grid=[2,2],color="white")
home_page_user_name_input_text = Text(home_page,text="Username: ",grid=[1,3],color="white")
home_page_username_input = TextBox(home_page,width=25,grid=[2,3])
home_page_password_input_text = Text(home_page,text="Password: ",grid=[1,4],color="white")
home_page_password_input = TextBox(home_page,width=25,grid=[2,4],hide_text=True)
home_page_login_button = PushButton(home_page,command=home_page_login,text="Login",grid=[3,5])
home_page_login_error = Text(home_page,text="Couldn't sign you in. Please try again",color="white",grid=[2,5],visible=False)
home_page_spacer2 = Text(home_page,text="",grid=[2,6])
home_page_signup_text = Text(home_page,text="Don't have a login? Make one here:",color="white",grid=[2,7])
home_page_signup_button = PushButton(home_page,command=home_to_signup,text="Sign up",grid=[3,7])
home_page_continue_text = Text(home_page,text="Continue to Search engine: ",color="white",grid=[7,2])
home_page_searching_button = PushButton(home_page,command=home_to_search,text="Search",grid=[7,3])
home_page_consolidation_text = Text(home_page,text="Continue to Consolidation: ",color="white",grid=[8,2])
home_page_consolidation_button = PushButton(home_page,command=home_to_consolidation,text="Consolidation",grid=[8,3])
quit_button = PushButton(home_page,command=quit_program,text="QUIT",grid=[20,20])
doer_buttong = PushButton(home_page,command=print_user_object,text="checker",grid=[40,40])

#logged in homepage
home_loggedin_page = Box(app,layout="grid",align="left",grid=[0,0],visible=False)
home_loggedin_title = Text(home_loggedin_page,text="Welcome to the sign language translator",grid=[0,0],color="white",align="left",size=20)
home_loggedin_spacer1 = Text(home_loggedin_page,text="",grid=[0,1])
home_loggedin_search_text = Text(home_loggedin_page,text="Click here to continue to Search page: ",color="white",grid=[0,2],align="left")
home_loggedin_search_button = PushButton(home_loggedin_page,command=loggedin_to_search,text="Continue to Search",grid=[0,3],align="left")
home_loggedin_consolidation_text = Text(home_loggedin_page,text="Click here to continue to Consolidation page",color="white",grid=[4,2],align="left")
home_loggedin_consolidation_button = PushButton(home_loggedin_page,command=loggedin_to_tailored_consolidation,text="Continue to Consolidation",grid=[4,3],align="left")
home_loggedin_spacer2 = Text(home_loggedin_page,text="",grid=[0,5])
home_loggedin_settings_button = PushButton(home_loggedin_page,command=loggedin_to_settings,text="Settings",grid=[10,10],align="left")
home_loggedin_logout_button = PushButton(home_loggedin_page,command=sign_out,text="Log out",grid=[0,10],align="left")
home_loggedin_logout_text = Text(home_loggedin_page,text="Progress will auto-save when you logout",grid=[0,9],color="white",align="left")
doer_buttong2 = PushButton(home_loggedin_page,command=print_user_object,text="checker",grid=[40,40])

#signup page objects
sign_up_page = Box(app,layout="grid",align="left",grid=[0,0],visible=False)
sign_up_title = Text(sign_up_page,text="Sign Up",size=20,color="white",grid=[0,0])
signup_to_home_button = PushButton(sign_up_page,command=signup_to_home,text="Return Home",grid=[0,10],align="left")
signup_text = Text(sign_up_page,text="Sign up Here: ",grid=[1,2],color="white")
signup_name_input_text = Text(sign_up_page,text="Full Name: ",grid=[0,3],color="white")
signup_name_input = TextBox(sign_up_page,width=25,grid=[1,3])
signup_user_name_input_text = Text(sign_up_page,text="Username: ",grid=[0,4],color="white")
signup_username_input = TextBox(sign_up_page,width=25,grid=[1,4])
signup_password_input_text = Text(sign_up_page,text="Password: ",grid=[0,5],color="white")
signup_password_input = TextBox(sign_up_page,width=25,grid=[1,5],hide_text=True)
signup_email_input_text = Text(sign_up_page,text="Email: ",grid=[0,6],color="white")
signup_email_input = TextBox(sign_up_page,width=25,grid=[1,6])
signup_button = PushButton(sign_up_page,command=sign_up_to_confirmation,text="Sign up",grid=[2,7])
signup_output_text = Text(sign_up_page,text="",grid=[3,2],color="white")

#confirmation of signup objects
confirmation_page = Box(app,layout="grid",align="left",grid=[0,0],visible=False)
confirmation_title = Text(confirmation_page,text="A code has been sent to the provided email",size=15,color="white",grid=[0,0],align="left")
confirmation_subtitle = Text(confirmation_page,text="Enter confirmation code",color="white",grid=[0,1],align="right")
confirmation_code_box = TextBox(confirmation_page,grid=[1,1],width=25)
confirmation_enter_button = PushButton(confirmation_page,command=confirming_sign_up_code,text="Enter",grid=[2,1])
confirmation_output_text = Text(confirmation_page,text="",color="white",grid=[0,3],align="right")
confirmation_continue_button = PushButton(confirmation_page,command=confirmation_to_home,text="Continue",grid=[1,3],visible=False)
confirmation_back_button = PushButton(confirmation_page,command=confiramtion_to_sign_up,text="Back",grid=[0,20])
confirmation_holder = Text(confirmation_page,text="",color="white",grid=[10,10],align="right",visible=False)

#search page objects
search_page = Box(app,layout="grid",align="left",grid=[0,0],visible=False)
search_page_title = Text(search_page,text="Search Page",grid=[0,0],color="white",size=20)
instructions = Text(search_page,text="Please enter a phrase to be searched:",grid=[1,1],color="white")
search_engine = TextBox(search_page,width=50,grid=[1,3])
enter_button = PushButton(search_page,command=search_phrase,text="Enter",grid=[2,3])
mic_on = PushButton(search_page,command=mic_input,text="Mic on",grid=[1,4])
spacer = Text(search_page,text = "      ",grid=[7,1])
alphabet_text = Text(search_page,text="Alphabet line: ",grid=[8,1],color="white")
alphabet = Combo(search_page,options=alphabet_list,command=alphabet_display,grid=[9,1])
alphabet_button = PushButton(search_page,command=alphabet_iteration,text="Search Letter",grid=[10,1],align="left")
alphabet_output = Text(search_page,text="output: ",grid=[10,3],align="left",color="white")
output_text = Text(search_page,text="",grid=[1,5],color="white",align="left")
signing_page_button = PushButton(search_page,command=search_to_search_result,text="Show Signing",grid=[2,5],visible=False)
spacer2 = Text(search_page,text="",grid=[1,6],color="white",align="left")
top_20_title = Text(search_page,text="Top 20 List: ",grid=[1,7],color="white",align="left")
top_20_output_text = Text(search_page,text="",grid=[1,8],color="white",align="left")
search_to_home_button = PushButton(search_page,command=search_to_home,text="Return Home",grid=[0,10])

#search result objects
search_result_page = Box(app,layout="grid",align="left",grid=[0,0],visible=False)
search_result_title = Text(search_result_page,text="Search Result Page",grid=[0,0],color="white",size=20)
search_result_user_input = Text(search_result_page,text="",color="white",grid=[0,2],align="left",size=15)
search_result_gif_output = Picture(search_result_page,image=None,grid=[2,4])
search_result_next_button = PushButton(search_result_page,command=iterate_search_result,text="Next",grid=[4,4],visible=False)
search_result_to_search_button = PushButton(search_result_page,command=search_result_to_search,text="Exit",grid=[0,20],align="left")
search_resut_current_output = Text(search_result_page,text="",color="white",grid=[0,3],align="left")

#consolidation of learning page
consolidation_page = Box(app,layout="grid",align="left",grid=[0,0],visible=False)
consolidation_page_title = Text(consolidation_page,text="Consolidation Page",grid=[0,0],color="white",size=20)
begin_practise_button = PushButton(consolidation_page,command=starting_consolidation,text="Begin Session",grid=[1,3])
begin_text = Text(consolidation_page,text="",color="white",grid=[0,3])
consolidation_to_home_button = PushButton(consolidation_page,command=consolidation_to_home,text="Exit",grid=[0,10],align="left")

consolidation_phrase_text = Text(consolidation_page,text="",grid=[2,5],color="white",visible=False,size=15)
consolidation_gif_output = Picture(consolidation_page,image=None,grid=[2,7])
consolidation_iterate_button = PushButton(consolidation_page,command=iterate_consolidation_output,text="Next signing",grid=[4,7],visible=False)
consolidation_reveal_desc = PushButton(consolidation_page,command=show_consolidation_phrase,text="Reveal phrase",grid=[2,8],visible=False)
consolidation_finish_text = Text(consolidation_page,text="To restart practising press the Begin Session button",color="white",grid=[2,9],visible=False)

#tailored consolidation page
tailored_consolidation_page = Box(app,layout="grid",align="left",grid=[0,0],visible=False)
tailored_consolidation_title = Text(tailored_consolidation_page,text="Tailored Consolidation",grid=[0,0],color="white",size=20)
tailored_consolidation_options = Text(tailored_consolidation_page,text="Please choose the method of practise: ",color="white",grid=[0,1])
tailored_phrase_then_desc = PushButton(tailored_consolidation_page,command=tailored_predict_desc,text="Predict the description",grid=[1,1])
tailored_desc_then_phrase = PushButton(tailored_consolidation_page,command=tailored_predict_phrase,text="Predict the phrase",grid=[2,1])
tailored_phrase_text = Text(tailored_consolidation_page,text="",color="white",grid=[4,2])
tailored_gif_output = Picture(tailored_consolidation_page,image=None,grid=[4,4])
tailored_iteration_button = PushButton(tailored_consolidation_page,command=tailored_consolidation,text="Next signing",grid=[5,4],visible=False)
tailored_reveal = PushButton(tailored_consolidation_page,command=show_tailored_phrase,text="Reveal",grid=[4,5],visible=False)
tailored_feedback_text = Text(tailored_consolidation_page,text="Did you guess correctly? ",color="white",grid=[4,6],align="right",visible=False)
tailored_correct_button = PushButton(tailored_consolidation_page,command=correct_tailored_consolidation,text="Right",grid=[5,6],visible=False)
tailored_incorrect_button = PushButton(tailored_consolidation_page,command=incorrect_tailored_consolidation,text="Wrong",grid=[6,6],visible=False)
tailored_consolidation_home = PushButton(tailored_consolidation_page,command=tailored_consolidation_to_loggedin,text="Home",grid=[0,20],align="left")

#settings page
settings_page = Box(app,layout="grid",align="left",grid=[0,0],visible=False)
settings_title = Text(settings_page,text="Settings Page",grid=[0,0],color="white",size=20,align="left")
settings_home_button = PushButton(settings_page,command=settings_to_loggedin,text="Home",grid=[0,20])
settings_name = Text(settings_page,text="Name: ",grid=[0,2],color="white",align="left")
settings_username = Text(settings_page,text="Username: ",grid=[0,4],color="white",align="left")
settings_date_joined = Text(settings_page,text="Date Joined: ",grid=[0,6],color="white",align="left")
settings_email = Text(settings_page,text="Email: ",grid=[0,8],color="white",align="left")
settings_spacer = Text(settings_page,text="                           ",grid=[1,1])

settings_old_password_text = Text(settings_page,text="Enter old password here: ",color="white",grid=[2,2],align="left")
settings_old_password_input = TextBox(settings_page,grid=[3,2],hide_text=True,width=30)
settings_new_password_text = Text(settings_page,text="Enter new password here: ",color="white",grid=[2,4],align="left")
settings_new_password_input = TextBox(settings_page,grid=[3,4],hide_text=True,width=30)
settings_confirm_password_text = Text(settings_page,text="Confirm new password: ",color="white",grid=[2,6],align="left")
settings_confirm_password_input = TextBox(settings_page,grid=[3,6],hide_text=True,width=30)
settings_change_password_button = PushButton(settings_page,command=change_password,text="Change password",grid=[4,6])
settings_password_error = Text(settings_page,text="",color="white",grid=[2,8])
settings_total_right = Text(settings_page,text="Total right answers: ",color="white",grid=[2,10],align="left")
settings_total_wrong = Text(settings_page,text="Total wrong answers: ",color="white",grid=[2,12],align="left")

app.display()