import json
import asyncio
import logging
from nio import AsyncClient, MatrixRoom, RoomMessageText

# Importing Holehe integration functions
from modules import check_email

# Configure logging
logging.basicConfig(level=logging.DEBUG, format="%(asctime)s - %(levelname)s - %(message)s")

# Load configuration
def load_config():
    try:
        with open('config.json', 'r') as file:
            return json.load(file)
    except FileNotFoundError:
        print("Configuration file 'config.json' not found.")
        exit()
    except json.JSONDecodeError:
        print("Error decoding the configuration file. Ensure 'config.json' is valid.")
        exit()

config = load_config()

class MatrixBot:
    def __init__(self, homeserver, username, password, hibp_api_key=None):
        self.client = AsyncClient(homeserver, username)
        self.password = password
        self.hibp_api_key = hibp_api_key
        self.commands = {
            "!email": self.email_check,
            "!help": self.show_help,
        }

    async def login(self):
        await self.client.login(self.password)
        print("Logged in successfully!")

    async def message_callback(self, room: MatrixRoom, event: RoomMessageText):
        if event.sender == self.client.user:  # Ignore messages from the bot itself
            return

        content = event.body.strip()
        logging.debug(f"Received message: {content} from {event.sender}")
        command, *args = content.split(maxsplit=1)
        args = args[0] if args else ""

        if command in self.commands:
            response = await self.commands[command](args)
            await self.client.room_send(
                room_id=room.room_id,
                message_type="m.room.message",
                content={"msgtype": "m.text", "body": response},
            )

    async def email_check(self, email):
        if not email:
            return "Usage: !email <email_address>"

        logging.info(f"Checking email: {email} with Holehe.")

        try:
            # Call the check_email function
            results = await check_email(email)

            if not results or results.strip() == "":
                logging.info(f"No results found for the email: {email}")
                return f"No results found for the email: {email}"

            logging.debug(f"Results for {email}: {results}")
            return results

        except Exception as e:
            logging.error(f"Error while checking email: {e}")
            return "An error occurred while checking the email. Please try again later."

    async def show_help(self, _):
        return "Available commands:\n" + "\n".join(self.commands.keys())

    async def run(self):
        self.client.add_event_callback(self.message_callback, RoomMessageText)
        await self.client.sync_forever(timeout=30000)

if __name__ == "__main__":
    async def main():
        bot = MatrixBot(
            homeserver=config["homeserver_url"],
            username=config["matrix_username"],
            password=config["matrix_password"],
            hibp_api_key=config.get("hibp_api_key")
        )
        await bot.login()
        await bot.run()

    asyncio.run(main())
