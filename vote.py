import smtplib, ssl
from xkcdpass import xkcd_password as xp
import selenium.webdriver
import time, random
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
"""
Passwords are generated with the xkcdpass library, which chooses random words of a given length.
Other methods are available, and easily implemented in the reciever loop

selenium and xkcdpass must be installed. (pip install selenium, pip install xkcdpass)

Selenium requires a browser driver in the python PATH folder. Alternatively, set the driver path manually.
google it. https://chromedriver.chromium.org/downloads


USAGE:

get a list of all mail addresses to send to in a file "vote.txt", one entry per line, no empty lines.
after changing the mail address to send from and optionally changing base_card_no, run the file

"""

# create a wordlist from the default wordfile
# use words between 5 and 9 letters long
wordfile = xp.locate_wordfile()
words = xp.generate_wordlist(wordfile=wordfile)


port = 465  # For SSL
smtp_server = "smtp.domeneshop.no" # might need changing
sender_email = "ENTER YOUR MAILADDRESS" # <---------     <---------     <---------

# get a list of email addresses.
# .txt-file must be formatted such that there is only one address per line.
# All spaces are removed
receiver_emails = list()
with open("vote.txt", "r") as f:
    while True:
        l = f.readline().replace(" ", "").replace("\n", "").replace("\t", "")
        if not l:
            break
        receiver_emails.append(l)
random.shuffle(receiver_emails)


# get the necessary user input
password = input("Type email password and press enter: ")
vote_username = input("Vote admin account username: ")
vote_password = input("Vote admin account password: ")

# do some setup for activating vote accounts
driver = selenium.webdriver.Chrome() # put path to chrome driver here if it is not in python PATH
driver.get("https://vote.timini.no/auth/login")
driver.find_element_by_name("username").send_keys(vote_username)
driver.find_element_by_name("password").send_keys(vote_password)
driver.find_element_by_name("password").submit()

driver.get("https://vote.timini.no/admin/create_user")

base_card_no = 2204 # smallest number for card numbers

uids = list()

def main():
    global base_card_no
    # setup the mail sending
    context = ssl.create_default_context()
    with smtplib.SMTP_SSL(smtp_server, port, context=context) as server:
        server.login(sender_email, password)

        # loop through users
        for i, receiver in enumerate(receiver_emails):
            # First, create credentials
            uid = "".join([a.capitalize() for a in (xp.generate_xkcdpassword(words, numwords = 3).split(" "))])
            pwd = "".join([a.capitalize() for a in (xp.generate_xkcdpassword(words, numwords = 4).split(" "))])

            # keep going untill a new uid is chosen. Extremely unlikely to ever run, but should be considered
            while uid in uids:
                uid = "".join([a.capitalize() for a in (xp.generate_xkcdpassword(words, numwords = 3).split(" "))])
            uids.append(uid)
            
            # then, open vote.timini.no to create an account with the uid and pwd
            driver.get("https://vote.timini.no/admin/create_user")
            time.sleep(3) #wait for the page to load
            driver.find_element_by_name("cardKey").send_keys(str(base_card_no + i))
            driver.find_element_by_name("username").send_keys(uid)
            driver.find_element_by_name("password").send_keys(pwd)
            driver.find_element_by_name("confirmPassword").send_keys(pwd)
            driver.find_element_by_name("confirmPassword").submit()

            # lastly, create the message and send it
            message = MIMEMultipart("alternative")
            message["Subject"] = "Påloggingsinformasjon til Genvors"
            message["From"] = sender_email
            message["To"] = receiver
            text = f"""\
            Hei,

            Under står din påloggingsinformasjon for stemming ved Generalvorsamlingen til Timini, torsdag 05.11.2020.
            Den er unik, tilfeldig generert, og dens eneste tilknytning til deg er gjennom denne mailen. 
            IKKE DEL DEN MED ANDRE!

            Brukernavn: {uid}
            Passord: {pwd}

            Stemmingen vil foregå på https://vote.timini.no 
            Koz og klemz,
            Valgteam ved Infomin"""
            message.attach(MIMEText(text, "plain"))
            try:
                server.sendmail(sender_email, receiver, message.as_string())
            except Exception as e: # 100 mails per session
                print(e)
                base_card_no += i
                main()
                break

main()
print("The highest card number was:", base_card_no + len(receiver_emails) - 1)
driver.close()
