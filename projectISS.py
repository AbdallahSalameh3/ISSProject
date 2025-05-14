import random
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import subprocess
import sys

# Install bcrypt
subprocess.check_call([sys.executable, "-m", "pip", "install", "bcrypt"])

# Install cryptography
subprocess.check_call([sys.executable, "-m", "pip", "install", "cryptography"])


try:
    import bcrypt
    print("bcrypt is installed.")
except ImportError:
    print("bcrypt is NOT installed.")

try:
    from cryptography.fernet import Fernet
    print("cryptography is installed.")
except ImportError:
    print("cryptography is NOT installed.")

# Fernet encryption key (in real apps, store securely!)
fernet_key = Fernet.generate_key()
fernet = Fernet(fernet_key)


# Dictionary to store users for registration and login
users = {}
elections = {}  # Store current elections
past_elections = {}  # Store ended elections

def send_email(recipient_email, otp):
    sender_email = "testprojectiss123@gmail.com"
    sender_password = "fonm lcuq bcif vcwv"

    subject = "Your OTP Code"
    body = f"Your OTP code is {otp}."

    message = MIMEMultipart()
    message['From'] = sender_email
    message['To'] = recipient_email
    message['Subject'] = subject
    message.attach(MIMEText(body, 'plain'))

    try:
        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.starttls()
        server.login(sender_email, sender_password)
        server.sendmail(sender_email, recipient_email, message.as_string())
        server.quit()
        print(f"OTP sent to {recipient_email}!")
    except smtplib.SMTPException as e:
        print(f"Error sending email: {e}")
    except Exception as e:
        print(f"Unexpected error: {e}")

def generate_otp():
    return str(random.randint(100000, 999999))  # Return as string for easier comparison

def register():
    print("\n--- Registering a New User ---")
    user_type = input("Enter user type (admin/student): ").lower()

    if user_type == 'admin':
        email = input("Enter your email (must be @gmail.com): ").strip()
        if not email.endswith('@gmail.com'):
            print("Admin email must end with @gmail.com")
            return
    elif user_type == 'student':
        email = input("Enter your email (must be @std.psut.edu.jo): ").strip()
        if not email.endswith('@std.psut.edu.jo'):
            print("Student email must end with @std.psut.edu.jo")
            return
    else:
        print("Invalid user type. Please enter either 'admin' or 'student'.")
        return

    password = input("Create a password: ").strip()

    otp = generate_otp()
    send_email(email, otp)
    try:
        user_otp = input("Enter the OTP sent to your email: ").strip()
    except ValueError:
        print("Invalid input. OTP must be a number.")
        return

    if user_otp != otp:
        print("Invalid OTP. Registration failed.")
        return

    users[email] = {
        'type': user_type,
        'password': bcrypt.hashpw(password.encode(), bcrypt.gensalt()),
        'voted': False,
        'voted_events': set()  # Initialize voted_events for student elections
    }
    print(f"Registration complete for {user_type}!")

def login():
    print("Logging in...")
    email = input("Enter your email: ")
    if email not in users:
        print("Email not found. Please register first.")
        return

    password = input("Enter your password: ")
    if not bcrypt.checkpw(password.encode(), users[email]['password']):
        print("Incorrect password.")
        return


    otp = generate_otp()
    send_email(email, otp)
    user_otp = input("Enter the OTP sent to your email: ").strip()

    if user_otp != otp:
        print("Invalid OTP. Login failed.")
        return

    print("Login successful!")

    if users[email]['type'] == 'admin':
        admin_menu(email)
    elif users[email]['type'] == 'student':
        student_menu(email)

def vote(email):
    if users[email]['voted']:
        print("You have already voted. You cannot vote again.")
        return

    candidate = input("Enter the name of the candidate you want to vote for: ")
    users[email]['voted'] = True
    print(f"Your vote for {candidate} has been recorded successfully!")

def menu():
    while True:
        print("\n1. Register")
        print("2. Login")
        print("3. Exit")
        choice = input("Choose an option: ")

        if choice == '1':
            register()
        elif choice == '2':
            login()
        elif choice == '3':
            print("Goodbye!")
            break
        else:
            print("Invalid choice. Please try again.")

def admin_menu(email):
    while True:
        print("\nAdmin Menu:")
        print("1. Create Election")
        print("2. View Current Elections")
        print("3. End Election")
        print("4. View Past Elections")
        print("5. Logout")

        choice = input("Choice: ").strip()
        if choice == '1':
            event_name = input("Enter election name: ").strip()
            candidates = input("Enter candidate names separated by commas: ").strip().split(',')
            elections[event_name] = {
                'candidates': {c.strip(): fernet.encrypt(b'0') for c in candidates},
                'active': True
            }
            print(f"Election '{event_name}' created.")
        elif choice == '2':
            for name, data in elections.items():
                if data['active']:
                    print(f"\n{name} - Candidates:")
                    for c, v in data['candidates'].items():
                        print(f"{c}: {int(fernet.decrypt(v).decode())} votes")
        elif choice == '3':
            to_end = input("Enter election name to end: ").strip()
            if to_end in elections and elections[to_end]['active']:
                elections[to_end]['active'] = False
                past_elections[to_end] = elections[to_end]
                del elections[to_end]
                print(f"Election '{to_end}' ended.")
            else:
                print("Election not found or already ended.")
        elif choice == '4':
            for name, data in past_elections.items():
                print(f"\n{name} - Past Election Results:")
                for c, v in data['candidates'].items():
                    print(f"{c}: {int(fernet.decrypt(v).decode())} votes")
        elif choice == '5':
            break
        else:
            print("Invalid choice.")

def student_menu(email):
    while True:
        print("\nStudent Menu:")
        print("1. Vote in Election")
        print("2. Logout")
        choice = input("Choice: ").strip()
        if choice == '1':
            available = [e for e in elections if elections[e]['active'] and e not in users[email]['voted_events']]
            if not available:
                print("No available elections to vote in.")
                continue

            print("Available Elections:")
            for i, name in enumerate(available):
                print(f"{i+1}. {name}")

            try:
                idx = int(input("Choose an election by number: ")) - 1
                selected = available[idx]
            except:
                print("Invalid selection.")
                continue

            print(f"\nCandidates in '{selected}':")
            for c in elections[selected]['candidates']:
                print(f"- {c}")
            vote_name = input("Enter candidate name to vote for: ").strip()

            if vote_name not in elections[selected]['candidates']:
                print("Invalid candidate.")
                continue

            otp = generate_otp()
            send_email(email, otp)
            entered_otp = input("Enter OTP to confirm your vote: ").strip()
            if entered_otp != otp:
                print("Incorrect OTP. Vote not recorded.")
                continue

            # Decrypt, increment, and re-encrypt vote count
            current_votes = int(fernet.decrypt(elections[selected]['candidates'][vote_name]).decode())
            current_votes += 1
            elections[selected]['candidates'][vote_name] = fernet.encrypt(str(current_votes).encode())
            users[email]['voted_events'].add(selected)
            print("Vote recorded successfully!")
        elif choice == '2':
            break
        else:
            print("Invalid choice.")
menu()