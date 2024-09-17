from encrypt import rsa, aes

from key_manager import KeyManager

from google_drive import GoogleDrive

from sync import Drive

from config_loader import DEFAULT_CONFIG as CONFIG
from config_loader import load_config, save_config
import ujson as json

from colorama import Fore, Style

from math import ceil,  floor

import concurrent.futures
import time

CEASED_TITLE = R"""
                       WELCOME TO
   _____   ______               _____   ______   _____                                                                                 
  / ____| |  ____|     /\      / ____| |  ____| |  __ \ 
 | |      | |__       /  \    | (___   | |__    | |  | |
 | |      |  __|     / /\ \    \___ \  |  __|   | |  | |
 | |____  | |____   / ____ \   ____) | | |____  | |__| |
  \_____| |______| /_/    \_\ |_____/  |______| |_____/
                                                            
   CEASED: CEASED: ENSURING A SECURELY ENCRYPTED DRIVE

"""



def print_block(title:str, rows:list[str], block_width:int=None):

    def unstyled_length(text:str):
        return len(text.replace(Fore.RED, '').replace(Fore.GREEN, '').replace(Fore.YELLOW, '').replace(Fore.BLUE, '').replace(Fore.MAGENTA, '').replace(Fore.CYAN, '').replace(Fore.WHITE, '').replace(Fore.BLACK, '').replace(Style.BRIGHT, '').replace(Style.DIM, '').replace(Style.NORMAL, '').replace(Style.RESET_ALL, ''))

    if block_width is None:
        block_width = max([unstyled_length(title)] + [unstyled_length(row) for row in rows]) + 4

    BORDER_STYLE = Style.DIM

    block_text = '\n'
    block_text += f"{BORDER_STYLE}+{'—'*block_width}+{Style.RESET_ALL}\n"

    def generate_title_row():
        title_length = unstyled_length(title)
        whitespace = (block_width - title_length) /2
        border_prefix = f"{BORDER_STYLE}|{' '*ceil(whitespace)}"
        border_suffix = f"{BORDER_STYLE}{' '*floor(whitespace)}|"
        return f"{border_prefix}{Style.RESET_ALL}{Style.BRIGHT}{title}{Style.RESET_ALL}{border_suffix}\n"
    
    block_text += generate_title_row()
    block_text += f"{BORDER_STYLE}|{' '*block_width}|{Style.RESET_ALL}\n"
    for row in rows:
        row_length = unstyled_length(row)
        border_prefix = f"{BORDER_STYLE}|{' '*2}"
        border_suffix = f"{BORDER_STYLE}{' '*(block_width-row_length-2)}|"
        block_text += f"{border_prefix}{Style.RESET_ALL}{row}{Style.RESET_ALL}{border_suffix}{Style.RESET_ALL}\n"
    
    block_text += f"{BORDER_STYLE}+{'—'*block_width}+{Style.RESET_ALL}"

    print(block_text)




def select_drive():
    def add_drive():
        label = input(f"Enter the {Style.BRIGHT}label{Style.RESET_ALL} of the drive: {Style.BRIGHT}")
        local_path = input(f"{Style.RESET_ALL}Enter the local path of the drive: ")
        remote_folder_id = input("Enter the remote folder id: ")

        drive = {
            'local_path': local_path,
            'remote_folder_id': remote_folder_id
        }

        CONFIG['folders_to_sync'][label] = drive
        save_config(CONFIG)
        
        select_drive()
    
    def remove_drive():
        drive_label = input(f"Enter the {Style.BRIGHT}name{Style.RESET_ALL} of the drive to remove: {Style.BRIGHT}{Fore.RED}")

        try:
            del CONFIG['folders_to_sync'][drive_label]
            save_config(CONFIG)
        except:
            print(f"{Fore.RED}Invalid drive number{Style.RESET_ALL}")
        
        select_drive()

    menu_items = [

    ]
    
    for i, drive in enumerate(CONFIG['folders_to_sync'].keys()):
        menu_items.append(f"{Style.DIM}{i+1}. {Style.NORMAL}{Fore.BLUE}{drive}")

    menu_items.append('')
    menu_items.append(f"{Style.DIM}+. {Style.NORMAL}{Fore.GREEN}Add Drive")
    menu_items.append(f"{Style.DIM}-. {Style.NORMAL}{Fore.RED}Remove Drive")


    print_block('Select Drive', menu_items)

    choice = input("Enter your choice: ")


    if choice == '+':
        add_drive()
    elif choice == '-':
        remove_drive()
    else:
        try:
            choice = int(choice)
            if choice > 0 and choice <= len(CONFIG['folders_to_sync']):
                label = list(CONFIG['folders_to_sync'].keys())[choice-1]
                return label
        except:
            pass



def spinner():
    SPINNER = ['|', '/', '-', '\\']
    frame = floor((time.time()*5) % 4)
    return SPINNER[frame]


def print_while_operating(function, message):
    with concurrent.futures.ThreadPoolExecutor() as executor:
        future = executor.submit(function)

        while not future.done():
            print(f"\n\n{Style.DIM}{message} {spinner()} \33[F\r\33[F\r{' '*40}\r", end='')
            time.sleep(0.1)

    result = future.result()
    print(f"\n{Style.DIM}{message} {Style.RESET_ALL}{Style.BRIGHT}{Fore.GREEN}Done{Style.RESET_ALL}")
    return result


def main():
    drive_label = None
    drive:Drive = None
    google_drive = GoogleDrive()
    key_manager = KeyManager(CONFIG['key_folder'])

    def main_menu():
        MENU_TEXT = {
            '1': Fore.BLUE+'Change Drive',
            '2': Fore.RED+'Pull',
            '3': Fore.GREEN+'Push',
            '4': Fore.CYAN+'Chat',
            '5': Fore.YELLOW+'Edit Config',
            '6': Style.DIM+'Exit'
        }
        rows = []

        for key, value in MENU_TEXT.items():
            rows.append(Style.DIM+key+'. '+Style.NORMAL+value)
        
        title = 'Main Menu'
        print_block(title, rows)

            
        choice = input("Enter your choice: ")
        return choice
    
    print(f"{Style.BRIGHT}{Fore.MAGENTA}{CEASED_TITLE}{Style.RESET_ALL}")

    choice = '1'
    while True:
        if choice == '1':
            drive_label = select_drive()
            drive_settings = CONFIG['folders_to_sync'][drive_label]


            def init_drive_class():
                return Drive(CONFIG, drive_settings['local_path'], drive_settings['remote_folder_id'], google_drive, key_manager)

            drive = print_while_operating(init_drive_class, "Initializing Drive")

        elif choice == '2':
            print_while_operating(drive.pull, "Pulling Drive")
        elif choice == '3':
            print_while_operating(drive.push, "Pushing Drive")
        elif choice == '4':
            
            menu = []
            for i, user in enumerate(drive.users):
                menu.append(f"{Style.DIM}{i+1}. {Style.NORMAL}{user}")

            print_block('Select User', menu)

            user_choice = input("Select User: ")
            print(drive.users)
            user_choice = drive.users[int(user_choice)-1]

            drive.chat.refresh()
            drive.chat.print_chat(user_choice)


        choice = main_menu()



if __name__ == "__main__":
    main()
