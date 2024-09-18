import time
import datetime
import concurrent.futures

from math import ceil,  floor
from colorama import Fore, Style

from encrypt import rsa
from key_manager import KeyManager
from google_drive import GoogleDrive, CredentialsNotFoundError
from sync import Drive
from config_loader import load_config, save_config

CEASED_TITLE = R"""
                       WELCOME TO
   _____   ______               _____   ______   _____
  / ____| |  ____|     /\      / ____| |  ____| |  __ \
 | |      | |__       /  \    | (___   | |__    | |  | |
 | |      |  __|     / /\ \    \___ \  |  __|   | |  | |
 | |____  | |____   / ____ \   ____) | | |____  | |__| |
  \_____| |______| /_/    \_\ |_____/  |______| |_____/

   CEASED: CEASED: ENSURING A SECURELY ENCRYPTED DRIVE"""



def print_block(title:str, rows:list[str], block_width:int=None):

    def unstyled_length(text:str):
        return len(text.replace(Fore.RED, '').replace(Fore.GREEN, '').replace(Fore.YELLOW, '').replace(Fore.BLUE, '').replace(Fore.MAGENTA, '').replace(Fore.CYAN, '').replace(Fore.WHITE, '').replace(Fore.BLACK, '').replace(Style.BRIGHT, '').replace(Style.DIM, '').replace(Style.NORMAL, '').replace(Style.RESET_ALL, ''))

    if block_width is None:
        block_width = max([unstyled_length(title)] + [unstyled_length(row) for row in rows]) + 4

    BORDER_STYLE = Style.DIM
    BORDER_TOP_BOTTOM = f"{BORDER_STYLE}+{'—'*block_width}+{Style.RESET_ALL}\n"

    block_text = Style.RESET_ALL+'\n'
    block_text += BORDER_TOP_BOTTOM

    def make_center_aligned_row(row:str):
        row_length = unstyled_length(row)
        whitespace = (block_width - row_length) /2
        prefix = f"{BORDER_STYLE}|{' '*ceil(whitespace)}"
        suffix = f"{BORDER_STYLE}{' '*floor(whitespace)}|"
        return f"{prefix}{Style.RESET_ALL}{row}{Style.RESET_ALL}{suffix}\n"

    def make_left_aligned_row(row:str):
        row_length = unstyled_length(row)
        prefix = f"{BORDER_STYLE}|{' '*2}"
        suffix = f"{BORDER_STYLE}{' '*(block_width-row_length-2)}|"
        return f"{prefix}{Style.RESET_ALL}{row}{Style.RESET_ALL}{suffix}\n"
    
    def make_right_aligned_row(row:str):
        row_length = unstyled_length(row)
        prefix = f"{BORDER_STYLE}|{' '*(block_width-row_length-2)}"
        suffix = f"{BORDER_STYLE}{' '*2}|"
        return f"{prefix}{Style.RESET_ALL}{row}{Style.RESET_ALL}{suffix}\n"

    def remove_render_instructions(row:str):
        return row.replace('$CENTERALIGNED$', '').replace('$RIGHTALIGNED$', '').replace('$LEFTALIGNED$', '')

    block_text += make_center_aligned_row(Style.BRIGHT+title)
    block_text += make_center_aligned_row('')

    for row in rows:
        text = remove_render_instructions(row)
        if '$CENTERALIGNED$' in row:
            block_text += make_center_aligned_row(text)
        elif '$RIGHTALIGNED$' in row:
            block_text += make_right_aligned_row(text)
        else:
            block_text += make_left_aligned_row(text)
    
    block_text += BORDER_TOP_BOTTOM.removesuffix('\n')

    print(block_text)

def execute_with_spinner(function, message):
    def spinner():
        SPINNER = ['|', '/', '-', '\\']
        frame = floor((time.time()*5) % 4)
        return SPINNER[frame]

    with concurrent.futures.ThreadPoolExecutor() as executor:
        future = executor.submit(function)

        while not future.done():
            print(f"\n{Style.RESET_ALL}{Style.DIM}{message}{Style.RESET_ALL}{Style.DIM} {spinner()} \33[F\r{' '*40}\r", end='')
            time.sleep(0.1)

    result = future.result()
    print(f"\n{Style.DIM}{message}{Style.RESET_ALL}{Style.DIM}: {Style.RESET_ALL}{Style.BRIGHT}{Fore.GREEN}Done{Style.RESET_ALL}")
    return result

class DriveMenu:
    def __init__(self, config:dict) -> None:
        self.config = config
    
    def display(self) -> str:
        menu_items = []
        
        for i, drive in enumerate(self.config['folders_to_sync'].keys()):
            menu_items.append(f"{Style.DIM}{i+1}. {Style.NORMAL}{Fore.BLUE}{drive}")

        menu_items.append('')
        menu_items.append(f"{Style.DIM}+. {Style.NORMAL}{Fore.GREEN}Add Drive")
        menu_items.append(f"{Style.DIM}-. {Style.NORMAL}{Fore.RED}Remove Drive")

        print_block('Select Drive', menu_items)
        choice = input("Enter your choice: ")

        if choice == '+':
            self.add_drive()
            return self.display()
        elif choice == '-':
            self.remove_drive()
            return self.display()
        elif choice == '':
            return None
        else:
            try:
                choice = int(choice)
                if choice > 0 and choice <= len(self.config['folders_to_sync']):
                    label = list(self.config['folders_to_sync'].keys())[choice-1]
                    return label
            except:
                pass

    def add_drive(self):
        label = input(f"Enter the {Style.BRIGHT}label{Style.RESET_ALL} of the drive: {Fore.MAGENTA}")
        local_path = input(f"{Style.RESET_ALL}Enter the local {Style.BRIGHT}path{Style.RESET_ALL} of the drive: {Fore.MAGENTA}")
        remote_folder_id = input(f"{Style.RESET_ALL}Enter the remote {Style.BRIGHT}folder id{Style.RESET_ALL}: {Fore.MAGENTA}")

        drive = {
            'local_path': local_path,
            'remote_folder_id': remote_folder_id
        }

        self.config['folders_to_sync'][label] = drive
        save_config(self.config)
    
    def remove_drive(self):
        drive_label = input(f"Enter the {Style.BRIGHT}label{Style.RESET_ALL} of the drive to remove: {Style.BRIGHT}{Fore.RED}")
        try:
            drive_cfg = self.config['folders_to_sync'][drive_label]
            local_path = drive_cfg['local_path']
            remote_folder_id = drive_cfg['remote_folder_id']
            drive = Drive(self.config, local_path, remote_folder_id, GoogleDrive(), KeyManager('keys/'))

            KeyManager('keys/').delete_key(f'archives/{drive.id}')

            del self.config['folders_to_sync'][drive_label]
            print(f"{Fore.RED}Drive removed from config{Style.RESET_ALL}")
        except:
            print(f"{Fore.GREEN}No drive removed{Style.RESET_ALL}")

class ChatMenu:
    def __init__(self, drive:Drive):
        self.drive = drive
        
    def display(self):
        option_rows = self.generate_option_rows()

        user_choice = self.user_select()
        choice = None
        while choice != '':
            menu_rows = []
            chat_history = self.format_chat_history(user_choice)

            for row in chat_history:
                menu_rows.append(row)
                        
            menu_rows.append('')
            menu_rows.append(f"$CENTERALIGNED${Style.BRIGHT}Options{Style.RESET_ALL}")
            for row in option_rows:
                menu_rows.append(row)

            print_block(
                f'Chatting with `{user_choice}`',
                menu_rows
            )

            choice = input("Enter your choice: ")

            if choice == '1':
                message = input(f"Enter your {Style.BRIGHT}message: {Style.RESET_ALL}{Fore.GREEN}")
                execute_with_spinner(lambda: self.drive.chat.send_message(user_choice, message), "Sending Message")
            
            elif choice == '2':
                execute_with_spinner(lambda: self.drive.request_archive_key(user_choice), "Requesting Key")

            elif choice == '3':
                execute_with_spinner(lambda: self.drive.send_archive_key(user_choice), "Sending Key")

            if choice == '4':
                execute_with_spinner(self.drive.chat.refresh, "Refreshing Chat")

    def generate_option_rows(self):
        MENU_TEXT = {
            '1': Fore.GREEN+'Compose message',
            '2': Fore.YELLOW+'Request drive key',
            '3': Fore.RED+'Send drive key',
            '4': Fore.CYAN+'Refresh'
        }
        option_rows = []

        for key, value in MENU_TEXT.items():
            option_rows.append(Style.DIM+key+'. '+Style.NORMAL+value)
        return option_rows

    def user_select(self):
        menu = []
        for i, user in enumerate(self.drive.users):
            menu.append(f"{Style.DIM}{i+1}. {Style.NORMAL}{user}")
        print_block('Select User to chat with', menu)
        user_choice = input("Select User: ")
        user_choice = list(self.drive.users.keys())[int(user_choice)-1]
        return user_choice

    def format_chat_history(self, user:str):
        rows = []

        chat_history = self.drive.chat.get_messages(user)
        chat_history = dict(sorted(chat_history.items(), key=lambda x: x[1]['timestamp']))
        for message_id, message_obj in chat_history.items():
            sender = message_obj['sender'].replace(self.drive.username, 'You')
            content = message_obj['content']
            timestamp = datetime.datetime.fromtimestamp(
                message_obj['timestamp']
            ).strftime('%Y-%m-%d %H:%M:%S')
            
            if sender == 'You':
                color_and_align = '$RIGHTALIGNED$'+Fore.GREEN
            elif sender == 'System':
                color_and_align = '$CENTERALIGNED$'+Fore.YELLOW+Style.DIM
            else:
                color_and_align = '$LEFTALIGNED$'+Fore.WHITE
            
            msg_head = Style.DIM+color_and_align+timestamp
            msg_body = color_and_align+content
            msg_feet = Style.DIM+color_and_align+'\u203E'*max([len(content), len(timestamp)])

            rows.append(msg_head)
            rows.append(msg_body)
            rows.append(msg_feet)
        return rows
    
class SettingsMenu:
    def __init__(self, config:dict) -> None:
        self.config = config

    def display(self):
        MENU_TEXT = {
            '1': 'Set Username',
        }
        rows = []
        for key, value in MENU_TEXT.items():
            rows.append(Style.DIM+key+'. '+Style.NORMAL+value)
        
        title = 'Settings'
        print_block(title, rows)

        choice = input("Enter your choice: ")
        if choice == '1':
            self.set_username()

    def set_username(self):
        username = input(f"Enter your {Style.BRIGHT}username{Style.RESET_ALL}: {Fore.GREEN}")
        self.config['username'] = username
        save_config(self.config)

class CLI:
    def __init__(self):
        self.drive_label:str = None
        self.drive:Drive = None

        while True:
            try:
                self.google_drive = GoogleDrive()
                break
            except CredentialsNotFoundError as e:
                print(f"{datetime.datetime.fromtimestamp((time.time())).isoformat()}{Fore.RED} {e}{Style.RESET_ALL}")
                time.sleep(1)
            
        self.key_manager = KeyManager('keys/')

        print(f"{Style.BRIGHT}{Fore.MAGENTA}{CEASED_TITLE}{Style.RESET_ALL}")

        try:
            self.config = load_config('config.yaml')
        except:
            print(f"\n{Fore.RED}Config file not found{Style.RESET_ALL}")
            COFNIG_TEMPLATE = {
                'folders_to_sync': {},
                'username': ''
            }
            SettingsMenu(COFNIG_TEMPLATE).set_username()
            self.config = load_config('config.yaml')
            private, public = rsa.generate_key_pair()
            self.key_manager.set_key('user/private', private)
            self.key_manager.set_key('user/public', public)

    def run(self):
        while True:
            choice = self.menu()

            if choice == '1':
                self.drive_label = DriveMenu(self.config).display()
                if not self.drive_label:
                    continue
                drive_settings = self.config['folders_to_sync'][self.drive_label]

                def init_drive_class():
                    return Drive(self.config, drive_settings['local_path'], drive_settings['remote_folder_id'], self.google_drive, self.key_manager)

                self.drive = execute_with_spinner(init_drive_class, f"Connecting to {self.drive_label}")

            if not self.drive:
                print(f"{Fore.RED}Please select a drive first{Style.RESET_ALL}")
                continue

            if choice == '2':
                execute_with_spinner(self.drive.pull, f"Pulling from {self.drive_label}")
            elif choice == '3':
                execute_with_spinner(self.drive.push, f"Pushing to {self.drive_label}")
            elif choice == '4':
                ChatMenu(self.drive).display()
                


    
    def menu(self):
        MENU_TEXT = {
            '1': Fore.BLUE+'Select Drive',
            '2': Fore.RED+'Pull',
            '3': Fore.GREEN+'Push',
            '4': Fore.YELLOW+'Chat',
            '5': Style.DIM+'Settings'
        }
        rows = []

        for key, value in MENU_TEXT.items():
            rows.append(Style.DIM+key+'. '+Style.NORMAL+value)
        
        title = f'{Fore.RED} Please Select a Drive' if not self.drive_label else f"Selectd Drive: {Fore.BLUE}{self.drive_label}"
        print_block(title, rows)

            
        choice = input("Enter your choice: ")
        return choice


if __name__ == "__main__":
    CLI().run()