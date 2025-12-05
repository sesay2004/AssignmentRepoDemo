import tkinter as tk
import tkinter.font as tkFont
from tkinter import Listbox, messagebox
from tkinter import ttk
from datetime import datetime, timedelta

#User database
users = {
    "sample": {
        "password": "123",
        "medications": [
            {
                "name": "Aspirin",
                "dosage": "100mg",
                "time": "8:00 AM",
                "symptoms": "Headache",
                "occurrence": "Daily",
                "days": []
            }
        ]
    }
}

#Global variables
current_user = None
reminders = {} # key: (username, med_name, time), value: afterID
current_schedule = { #stores current schedule selections
    "time": None,
    "occurrence": None,
    "days": []
}

#Main window configurations
mainWindow = tk.Tk()
mainWindow.title("MediTrack Login form")
mainWindow.geometry("350x450")
mainWindow.configure(bg = '#F0F0F0')
font1 = tkFont.Font(family = "Arial", size = 12, weight = tkFont.NORMAL)

#Dashboard Window configurations
dashboard = tk.Toplevel(mainWindow)
dashboard.title("MediTrack dashboard")
dashboard.geometry("800x450")
dashboard.configure(bg = '#F0F0F0')
dashboard.withdraw()

#Sign-in Window
signIn = tk.Toplevel(mainWindow)
signIn.title("Create new User")
signIn.geometry("350x450")
signIn.configure(bg = '#F0F0F0')
signIn.withdraw()



''' TODO: Implement history window
        CODE:
        historyWindow = tk.Toplevel(dashboard)
        historyWindow.title("Medication History")
        historyWindow.geometry("350x450")
        historyWindow.configure(bg = '#F0F0F0')
        historyWindow.withdraw() '''

label = tk.Label(mainWindow, text = "MediTrack", bg= "#F5D5F7", font = font1)
label.place(x= 125,y=0)

def login():
    global users
    global current_user
    username = userEntry.get().strip()
    password = passEntry.get().strip()
    print("attempted login:", username, password)
   
    if username in users and users[username]["password"] == password:
        current_user = username
        messagebox.showinfo(title = "Login Successful", message = f"Welcome back, {username}!")
        dashboard.deiconify()
        mainWindow.withdraw()
        updateMedListbox()
    else:
        messagebox.showinfo(title = "Login Failed", message = "Invalid username or password")
           
def signUp():
    mainWindow.withdraw()
    signIn.deiconify()
   
def createUser():  
    username = signUserEntry.get().strip()
    password = signPassEntry.get().strip()
    confirmPass = passRentry.get().strip()
   
    if username in users:
        messagebox.showinfo(title = "Sign up failed", message = "Account with this user already exists")
       
    elif password != confirmPass:
         messagebox.showinfo(title = "Invalid Password", message = "Passwords don't match")
         
    else:
        users[username] = {"password": password, "medications": []}
        print(users)
        messagebox.showinfo(title = "User created", message = "Redirecting back to login")
        signIn.withdraw()
        mainWindow.deiconify()

#adds medication to the list if not already present
def addMedication():
    global current_user
    user_medications = users[current_user].setdefault("medications", [])

    med_input = medicationEntry.get().strip()
    dosage_input = dosageEntry.get().strip()
    symptoms_input = symptomsEntry.get().strip()

    #input validation
    if not med_input:
        messagebox.showinfo(title="Missing input", message="Medication cannot be empty!")
        return
   
    if not dosage_input:
        messagebox.showinfo(title="Missing input", message="Please enter the dosage")
        return
   
    if not current_schedule["time"]:
        messagebox.showinfo(title="Missing input", message="Please set a schedule for the medication")
        return
   
    if parse_time(current_schedule["time"]) is None:
        messagebox.showinfo(title="Invalid Time Format", message="Please click 'Set Schedule' and choose a time and occurrence for the medication")
        return

    #normalize medication name for duplicate check
    med_norm = med_input.casefold()

    #duplicate check
    is_duplicate = any(med.get("name", "").strip().casefold() == med_norm
                       for med in user_medications)
    if is_duplicate:
        messagebox.showinfo(title="Duplicate Entry", message=f"{med_input} is already in your medications!")
        return

    #add medication to the list
    new_med = {
        "name": med_input,
        "dosage": dosage_input,
        "time": current_schedule["time"],
        "symptoms": symptoms_input,
        "occurrence": current_schedule["occurrence"],
        "days": current_schedule["days"],
    }
   
    user_medications.append(new_med)
    users[current_user]["medications"] = user_medications

    scheduleReminder(current_user, new_med)

    #refresh listbox
    updateMedListbox()

    #clear entries
    medicationEntry.delete(0, tk.END)
    dosageEntry.delete(0, tk.END)
    symptomsEntry.delete(0, tk.END)

    #confirmation message
    messagebox.showinfo(title = "Medication Added", message = f"{med_input} is added to your medications!")
    print(f"[DEBUG] Current medications for {current_user}: {users[current_user]['medications']}")

#function to remove selected medication from listbox and user data
def onMedSelect(event):
    selection = medListbox.curselection()

    if selection and selection[0] != 0:
        removeMedButton.place(x=350, y=390, width=200, height=30)
    else:
        removeMedButton.place_forget()
    selection = medListbox.curselection()

    medListbox.bind('<<ListboxSelect>>', onMedSelect)


#function to confirm and remove medication
def confirmRemoveMedication():
    global current_user

    selection = medListbox.curselection()

    if not selection or selection[0] == 0:
        return
   
    med_index = selection[0] - 1
    med_name = users[current_user]["medications"][med_index]["name"]

    answer = messagebox.askyesno(title="Confirm Removal", message=f"Are you sure you want to remove {med_name}?")
    if answer:
        users[current_user]["medications"].pop(med_index)
        updateMedListbox()
        removeMedButton.place_forget()

#function to update the medication listbox
def updateMedListbox():
    global current_user
    medListbox.delete(0, tk.END)

    medListbox.insert(tk.END, "Name | Dose | Time | Symptoms")
    medListbox.itemconfig(0, {'fg': 'white', 'bg': 'black'})

    user_medications = users[current_user].get("medications", [])
    for med in user_medications:
        #if symptoms is empty, display "None"
        symptoms_display = med.get("symptoms", "").strip() or "None"
        line = f"{med['name']} | {med['dosage']} | {med['time']} | {symptoms_display}"
        medListbox.insert(tk.END, line)


#parses the time input string into a real datetime object
def parse_time(time_str):
    try:
        parsed = datetime.strptime(time_str, "%I:%M %p")
        return parsed.time()
    except ValueError:
        return None

#function to calculate milliseconds until the next occurrence of the specified time
def seconds_until(time_str):
    try:
        now = datetime.now()
        medTime = datetime.strptime(time_str, "%I:%M %p") #parse time string
        medDate = now.replace(hour=medTime.hour, minute=medTime.minute, second=0, microsecond=0)

        if medDate <= now:
            medDate += timedelta(days=1) #schedule for next day if time has passed

        return int((medDate - now).total_seconds()*1000) #convert to milliseconds
   
    except ValueError:
        return None



# function to schedule reminders (TC01 + TC02)
def scheduleReminder(username, med):
    # get time string and calculate delay using YOUR helper
    time_str = med['time']
    delay_ms = seconds_until(time_str)
    if not delay_ms or delay_ms <= 0:
        print(f"[ERROR] Invalid time format for medication {med['name']}: {time_str}")
        return

    # unique key for each reminder (so we can cancel/reschedule correctly)
    key = (username, med['name'], time_str)

    # cancel existing reminder if present
    if key in reminders:
        try:
            dashboard.after_cancel(reminders[key])
        except Exception:
            pass
        reminders.pop(key, None)

    # function to show reminder popup
    def notify():
        popup = tk.Toplevel(dashboard)
        popup.title("Medication Reminder")
        popup.geometry("300x150")
        tk.Label(popup, text=f"Time to take {med['name']} ({med['dosage']})", font=font1).pack(pady=20)
       
        #function to delay the reminder popup
        def waitButton():
            popup.destroy()
       
            #delaying the reminder for 1 minute
            waitDelay = 60*1000
            # <CHANGE> Changed showReminder to notify to call the correct function
            remindID = dashboard.after(waitDelay, notify)
            reminders[key] = remindID
           
        def okButton():
            popup.destroy()
            scheduleReminder(username, med)
           
        tk.Button(popup, text="OK", command=okButton).pack(pady=10)
        tk.Button(popup, text = "Wait (1min)", command = waitButton).pack(pady = 5)    

    # <CHANGE> Changed showReminder to notify to call the correct function
    remindID = dashboard.after(delay_ms, notify) #schedule the reminder
    reminders[key] = remindID #store the reminder ID
    print(f"[DEBUG] Scheduled reminder for {username} to take {med['name']} in {delay_ms/1000:.2f} seconds.")


#callback function when schedule is chosen
def on_schedule_chosen(time_str, occurence, days):
    #update current schedule
    current_schedule["time"] = time_str
    current_schedule["occurrence"] = occurence
    current_schedule["days"] = days

    #update time entry field
    print("[DEBUG] Selected schedule:", time_str, occurence, days)


#function to open scheduler window
def open_scheduler(on_done):

    #create scheduler window
    window = tk.Toplevel(dashboard)
    window.title("Schedule Your Medication")
    window.geometry("320x260")
    window.configure(bg='#F0F0F0')
    window.grab_set()

    # --- time selection widgets ---
    tk.Label(window, text="Time:", bg="#F0F0F0", font=font1).place(x=20, y=20)

    # default time values
    hourVar = tk.StringVar(value="8")
    minuteVar = tk.StringVar(value="00")
    ampmVar = tk.StringVar(value="AM")

    # options for time selection
    hours = [f"{i}" for i in range(1, 13)]
    minutes = [f"{i:02d}" for i in range(0, 60)]
    ampm = ["AM", "PM"]

    #time selection comboboxes
    hours_box = ttk.Combobox(window, textvariable=hourVar, values=hours, width=5, state="readonly")
    hours_box.place(x=80, y=20)

    tk.Label(window, text=":", bg="#F0F0F0", font=font1).place(x=140, y=20)

    minute_box = ttk.Combobox(window, textvariable=minuteVar, values=minutes, width=5, state="readonly")
    minute_box.place(x=135, y=20)

    ampm_box = ttk.Combobox(window, textvariable=ampmVar, values=ampm, width=5, state="readonly")
    ampm_box.place(x=195, y=20)

    tk.Label(window, text="Occurrrence:", bg="#F0F0F0", font=font1).place(x=20, y=70)
   
    # occurrence selection combobox
    occurrenceVar = tk.StringVar(value="Daily")
    occurrence_box = ttk.Combobox(window, textvariable=occurrenceVar,
                                  values=["Once", "Daily", "Monthly", "Custom days"],
                                  state="readonly",
                                  width=15)
    occurrence_box.place(x=120, y=70)

    # --- Optional specific days selection ---

    tk.Label(window, text="(Optional) Select Days:", bg="#F0F0F0", font=font1).place(x=20, y=110)

    days_frame = tk.Frame(window, bg="#F0F0F0")
    days_frame.place(x=20, y=135)

    dayVars = {}
    days = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
    for i, name in enumerate(days):
        var = tk.BooleanVar(value=False)
        chk = tk.Checkbutton(days_frame, text=name, variable=var, bg="#F0F0F0")
        chk.grid(row=0, column=i, padx=2)
        dayVars[name] = var

# --- Save and Cancel buttons ---

    def on_save():
        hour = hourVar.get()
        minute = minuteVar.get()
        ampm = ampmVar.get()
        occurrence = occurrenceVar.get()

        time_str = f"{int(hour)}:{minute} {ampm}"
        selected_days = [name for name, var in dayVars.items() if var.get()]

        on_done(time_str, occurrence, selected_days)
        window.destroy()
   
    def on_cancel():
        window.destroy()
   
    tk.Button(window, text="Save", bg="#F5D5F7", font=font1, command=on_save).place(x=70, y=200, width=80, height=30)
    tk.Button(window, text="Cancel", bg="#F5D5F7", font=font1, command=on_cancel).place(x=170, y=200, width=80, height=30)



# ... existing code ...



# --- widgets main login window ---

userLabel = tk.Label(mainWindow, text = "Username", bg = "#F5D5F7", font = font1)
passLabel = tk.Label(mainWindow, text = "Password", bg = "#F5D5F7", font = font1)
userEntry = tk.Entry(mainWindow)
passEntry = tk.Entry(mainWindow, show = "*")
loginButton = tk.Button(mainWindow, text = "Login", bg = "#F5D5F7", font = font1, command = login)
signUpButton = tk.Button(mainWindow, text = "Sign up", bg = "#F5D5F7", font = font1, command = signUp)

# --- widgets create user window ---

signUserEntryL = tk.Label(signIn, text = "Enter Username", bg = "#F5D5F7", font = font1)
signPassEntryL = tk.Label(signIn, text = "Enter Password", bg = "#F5D5F7", font = font1)
passRentryL = tk.Label(signIn, text = "Confirm Password", bg = "#F5D5F7", font = font1)
signUserEntry = tk.Entry(signIn)
signPassEntry = tk.Entry(signIn, show = "*")
passRentry = tk.Entry(signIn,show = "*")
createUserButton = tk.Button(signIn, text = "Create User", bg = "#F5D5F7", font = font1, command = createUser)
backButton = tk.Button(signIn, text="Go Back", bg="#F5D5F7", font=font1, command=lambda: [signIn.withdraw(), mainWindow.deiconify()])


# --- widgets dashboard window ---

#Entries
medicationEntry = tk.Entry(dashboard)
medicationEntryL = tk.Label(dashboard, text = "Input Medications", bg = "#F5D5F7", font = font1)
dosageEntry = tk.Entry(dashboard)
dosageEntryL = tk.Label(dashboard, text = "Dosage", bg = "#F5D5F7", font = font1)
symptomsEntry = tk.Entry(dashboard)
symptomsEntryL = tk.Label(dashboard, text = "Symptoms", bg = "#F5D5F7", font = font1)

#buttons
scheduleButton = tk.Button(
    dashboard,
    text="Set Schedule",
    bg="#F5D5F7",
    font=font1,
    command=lambda: open_scheduler(on_schedule_chosen)
)

addMedButton = tk.Button(dashboard, text="Add Medication", bg="#F5D5F7", font=font1, command=addMedication)

#Listbox and Scrollbar for medications
medListbox = tk.Listbox(dashboard, font=font1)
scrollbar = tk.Scrollbar(dashboard, orient=tk.VERTICAL)

medListbox.config(yscrollcommand=scrollbar.set)
scrollbar.config(command=medListbox.yview)

#remove medication button appears when a medication is selected
removeMedButton = tk.Button(dashboard, text="Remove Selected Medication", font=font1, bg="#F5D5F7", command=confirmRemoveMedication)
removeMedButton.place(x=350, y=390, width=200, height=30)
removeMedButton.place_forget()



'''TODO: Implement history window and its button
historyButton = tk.Button(dashboard, text="View Medication History", bg="#F5D5F7", font=font1, command=lambda: [dashboard.withdraw(), historyWindow.deiconify()])'''


# --- positions for labels and buttons ---

#login
loginButton.place(x = 125, y = 100)
signUpButton.place(x = 125, y = 250)
userLabel.place(x=50, y=150)
userEntry.place(x=130 , y=150)
passLabel.place(x=50, y=190)
passEntry.place(x=130, y= 190)
#create
signUserEntry.place(x=195, y= 150)
signPassEntry.place(x=195, y= 190)
passRentry.place(x=195,y=230)
signUserEntryL.place(x=30, y=150)
signPassEntryL.place(x=30, y=190)
passRentryL.place(x=30, y=230)
createUserButton.place(x = 130, y= 300)
backButton.place(x=130, y=350)
#dashboard
medicationEntryL.place(x=20, y=30)
medicationEntry.place(x=155, y=30, width=140)

dosageEntryL.place(x=20, y=80)
dosageEntry.place(x=155, y=80, width=140)

symptomsEntryL.place(x=20, y=130)
symptomsEntry.place(x=155, y=130, width=140)

scheduleButton.place(x=20, y=180, width=110, height=30)
addMedButton.place(x=155, y=180, width=145, height=30)

medListbox.place(x=350, y=30, width=400, height=350)
scrollbar.place(x=750, y=30, width=20, height=350)


'''TODO: Implement history window layout'''

def onMedSelect(event):
    selection = medListbox.curselection()

    if selection and selection[0] != 0:
        removeMedButton.place(x=350, y=390, width=215, height=30)
    else:
        removeMedButton.place_forget()
    selection = medListbox.curselection()

medListbox.bind('<<ListboxSelect>>', onMedSelect)

   
mainWindow.mainloop()
