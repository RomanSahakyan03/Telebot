# TypeTalk

TypeTalk is a Telegram chat bot that connects users anonymously based on their parameters, such as age, sex, MBTI type, and region. It leverages the Telegram API along with various Python modules to facilitate these connections.

## Installation

1. Ensure you have Python 3.10.10 installed on your system.
2. Clone the repository from GitHub.
3. Install the required modules by running `pip install -r requirements.txt`.

## Configuration

To configure TypeTalk, follow these steps:

1. Obtain a Telegram API token from the [Telegram BotFather](https://core.telegram.org/bots#3-how-do-i-create-a-bot).
2. Set the `TELEGRAM_API_TOKEN` environment variable to your Telegram API token.
3. Specify the connection details for your Redis server in the `config.py` file.

## Usage

1. Start the TypeTalk bot by running `python main.py`.
2. Interact with the bot through Telegram by sending commands and providing your parameters.
3. TypeTalk will match you with another user based on compatible parameters and establish an anonymous connection.

### Available Commands

- `/start`: Begin the TypeTalk conversation.
- `/settings`: 
- `/about <sex>`: 
- `/shareprofil <mbti>`: 
- `/stop <region>`: 

## File Structure

```
TypeTalk/
├── app.py
├── db.py
├── settings.py
├── send_data.py
├── edit_data.py
├── typetalk_texts.json
├── userdata.db
├── requirements.txt
└── README.md
```

- `app.py`: Entry point for running the TypeTalk bot.
- `db.py`: Contains a class for handling SQLite database operations.
- `settings.py`: Contains functions for managing general settings (calls once).
- `send_data.py`: Handles sending data to users.
- `edit_data.py`: Handles editing user data.
- `typetalk_texts.json`: JSON file containing text templates for the bot's responses and system texts in multiple languages.
- `userdata.db`: SQLite database file for storing user data.
- `requirements.txt`: List of Python dependencies required for running the project.
- `README.md`: This file.

## Contributing

If you would like to contribute to TypeTalk, please follow these guidelines:

1. Fork the repository and create a new branch.
2. Make your changes and ensure the code passes all tests.
3. Submit a pull request, describing the changes you have made.

## Troubleshooting

If you encounter any issues while running TypeTalk, try the following troubleshooting steps:

1. Ensure you have provided the correct Telegram API token and Redis server connection details.
2. Check your internet connection and ensure the necessary ports are open.
3. Verify that you have the required Python version (3.10.10) and modules installed.

## License

TypeTalk is released under the [MIT License](LICENSE).

## Acknowledgments

- The Telegram API for providing the platform for building the chat bot.
- The Python community for developing and maintaining the modules used in this project.