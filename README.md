# ceased
Ceased: Ceased: Ensuring a securely encrypted drive

## Installation

### Prerequisites
- git
- python
- a google account

### Setup Project

1. **Create a project**

    https://console.cloud.google.com/projectcreate

2. **Enable the Google Drive API**
    
    a. https://console.cloud.google.com/marketplace/product/google/drive.googleapis.com

    b. Make sure you have selected your project

    c. Enable

3. **Create Credentials**
    https://console.cloud.google.com/apis/credential

    create api key


### Installation script
```bash
git clone https://github.com/McEsgow/ceased
cd ceased
python -m venv .venv
.venv\Scripts\activate
python -m pip install requirements.txt
```

## Config

## Run

```bash
cd ceased
.venv\Scripts\activate
main.py
```



## How its working

### messages 

```json
{
    "user_1": {
        "message_id": {
            "timestamp": 123,
            "content": "Hello",
            "sent": false
        }
    }
}


```