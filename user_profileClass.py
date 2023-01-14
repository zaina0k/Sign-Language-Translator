from datetime import date
#classes
class User:
    """class that creates user objects"""
    user_counter = 0
    def __init__(self,name,username,password,email,user_number,date_joined,started_TL,learning_path,total_right,total_wrong):
        """initialising the class"""
        today = date.today()
        self.name = name
        self.username = username
        self.password = password
        self.email = email
        if total_right == None:
            self.total_right = 0
        else:
            self.total_right = total_right
        if total_wrong == None:
            self.total_wrong = 0
        else:
            self.total_wrong = total_wrong
        if learning_path != None:
            try:
                self.learning_path = ast.literal_eval(learning_path)
            except:
                self.learning_path = learning_path
        else:
            self.learning_path = None
        if started_TL == None:
            self.started_TL = "No"
        else:
            self.started_TL = started_TL

        if date_joined == None:
            self.date_joined = today.strftime("%d/%m/%Y")
        else:
            self.date_joined = date_joined
        if user_number == None:
            self.user_number = User.user_counter + 1
            User.user_counter += 1
        else:
            self.user_number = user_number
    def __str__(self):
        """print method shows all the values of the object"""
        print_str = ""
        print_str+= "user number: " + str(self.user_number) + "\n"
        print_str+= "name: " + str(self.name)+ "\n"
        print_str+= "username: " + str(self.username)+ "\n"
        print_str+= "password: " + str(self.password)+ "\n"
        print_str+= "date joined: " + str(self.date_joined)+ "\n"
        print_str+= "email: " + str(self.email) + "\n"
        print_str+= "started tailored learning? " + str(self.started_TL) + "\n"
        print_str+= "current learning path: "+ str(self.learning_path)+ "\n"
        print_str+= "total right: " + str(self.total_right) + "\n"
        print_str+= "total wrong: " + str(self.total_wrong)
        return print_str