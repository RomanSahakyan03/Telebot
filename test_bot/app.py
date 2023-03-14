import requests
import json

# Set up API endpoint and bot token
api_endpoint = "https://api.telegram.org/bot"
bot_token = "6230593358:AAFqvivxeQtuW2q2zQLQsJNWC5_xuvqEsHA"
send_message_url = api_endpoint + bot_token + "/sendMessage"
inline_keyboard = api_endpoint + bot_token + "/InlineKeyboardMarkup"

# Set up message parameters
chat_id = "781874113" # Replace with the ID of the user or group you want to send the message to
message_text = "Select Your MBTI type!" # Replace with the message you want to send


# Create the keyboard
keyboard = {
    "inline_keyboard": [
        [{"text": "INTJ", "callback_data": "1"},
         {"text": "INFJ", "callback_data": "2"},
         {"text": "ISTJ", "callback_data": "3"},
         {"text": "ISTP", "callback_data": "4"}],
        [{"text": "INTP", "callback_data": "5"},
         {"text": "INFP", "callback_data": "6"},
         {"text": "ISFJ", "callback_data": "7"},
         {"text": "ISFP", "callback_data": "8"}],
        [{"text": "ENTJ", "callback_data": "9"},
         {"text": "ENFJ", "callback_data": "10"},
         {"text": "ESTJ", "callback_data": "11"},
         {"text": "ESTP", "callback_data": "12"}],
        [{"text": "ENTP", "callback_data": "13"},
         {"text": "ENFP", "callback_data": "14"},
         {"text": "ESFJ", "callback_data": "15"},
         {"text": "ESFP", "callback_data": "16"}]
    ]
}

# Convert the keyboard to JSON format
keyboard_json = json.dumps(keyboard)


# Construct JSON data for message
data = {
    "chat_id": chat_id,
    "text": message_text,
    'reply_markup': keyboard_json
}


# Send the message
response = requests.post(send_message_url, data=data)

# Print response status code and content
#print("Response status code:", response.status_code)
#print("Response content:", response.content)