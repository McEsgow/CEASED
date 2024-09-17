# CEASED: CEASED: Ensuring a securely encrypted drive

CEASED ensures that your files stored in Google Drive are securely encrypted. The system allows you to synchronize local directories with encrypted remote backups on Google Drive, ensuring your data remains confidential even if the cloud service is compromised. CEASED also supports chatting with others with access to a shared google drive foleder, as well as securely exchanging encryption keys.

## Features
- **Encrypted Sync**: Sync local folders with Google Drive while encrypting files to ensure privacy. All files are encrypted before they even touch Google's servers.
- **Drive Management**: Add or remove folders to be synced with encrypted Google Drive folders.
- **Key Management**: Securely handle and distribute encryption keys.
- **Chat Interface**: Secure communication for sharing keys or updates related to the encrypted drive.

## To do

- **GUI**

## Installation

### Prerequisites
- Git
- Python
- A Google account with access to Google Cloud Console


### Installation script
```bash
git clone https://github.com/McEsgow/ceased
cd ceased
python -m venv .venv
.venv\Scripts\activate
python -m pip install requirements.txt
```

### Or use the precompiled binaries

You can download precompiled binaries from the [releases page](https://github.com/McEsgow/ceased/releases).

### Setting up Google Drive Credentials

To use Google Drive with CEASED, you need to create credentials from the Google Cloud Console:

1. **Create a Google Cloud Project**
    1. Visit [Google Cloud Console](https://console.cloud.google.com/projectcreate).

    2. Name your project (e.g., `ceased-drive-encryption`).    

    3. Click **Create**.

2. **Enable the Google Drive API**    
    1. Go to the [Google Drive API page](https://console.cloud.google.com/marketplace/product/google/drive.googleapis.com).

    2. Ensure your project is selected in the top-left corner.

    3. Click **Enable**.

3. **Create OAuth Credentials**
    1. Go to [APIs & Services > Credentials](https://console.cloud.google.com/apis/credentials).

    2. Ensure your project is selected in the top-left corner.

    3. Click **Create Credentials**, then select **OAuth Client ID**.

    4. Choose `Desktop App` as the Application Type and click **Create**

    5. Download the generated `client_secret_****.json`.

    6. Move this file to your `ceased/auth` directory and rename it to `credentials.json`.



## Usage

### Running with Python

To start CEASED with Python, use:

```bash
# From the project root
source .venv/bin/activate  # On Windows use: .venv\Scripts\activate
python scripts/main.py
```

### Running Precompiled Binary

If you're using the precompiled version:

```bash
# Navigate to the project folder
./ceased.exe
```

### CLI Overview

Once CEASED is running, you can interact with the application through its command-line interface (CLI). Here's an overview of the key options:

1. **Select Drive**: Choose a drive to sync by selecting one of the configured Google Drive folders.
   - If no drives are configured, you can add one by selecting the **Add Drive** option.
   - You can also remove a configured drive by selecting the **Remove Drive** option.

2. **Pull**: This option allows you to pull data from the encrypted Google Drive folder and sync it to your local folder. The data remains encrypted during transmission.

3. **Push**: Use this option to push data from your local folder to the Google Drive folder, encrypting the files before they are uploaded.

4. **Chat**: Securely communicate with other users. The chat interface allows you to:
   - Send and receive messages.
   - Request the encryption key for a shared drive.
   - Send your encryption key to another user.
   - Refresh the chat to view new messages.

5. **Settings**: Configure CEASED settings, such as updating your username.



<details>

1. **Select Drive**
   - When you choose this option, the CLI will display a list of available drives configured in `config.yaml`.
   - After selecting a drive, you can pull from or push to this drive.

2. **Pull**
   - This option downloads the encrypted files from Google Drive to your local system.
   - The files are decrypted locally after the download completes.

3. **Push**
   - Use this to upload new or updated files from your local system to Google Drive.
   - All files are encrypted before they are uploaded to the cloud.

4. **Chat**
   - After selecting a drive, the **Chat** menu enables secure messaging with other users who have access to the same drive.
   - You can perform the following actions:
     - **Compose Message**: Send a message to another user.
     - **Request Drive Key**: Request the encryption key from another user to access their files.
     - **Send Drive Key**: Send your encryption key to a user.
     - **Refresh Chat**: View new messages in the chat interface.
   - The chat history is displayed with timestamps and includes both user and system messages (e.g., when a key is requested or sent).

5. **Settings**
   - In the **Settings** menu, you can update your username for use within CEASED.
   - The username is saved in the `config.yaml` file and is used for identifying you in the chat interface.


</details>

## Example Workflow

1. **Start the application** and select a drive:
    ```bash
    1. Select Drive
    ```

2. **Pull the latest files** from Google Drive:
    ```bash
    2. Pull
    ```

3. **Make changes to your local files**, then push them back to Google Drive:
    ```bash
    3. Push
    ```

4. **Use the chat interface** to send a message or exchange encryption keys:
    ```bash
    4. Chat
    ```