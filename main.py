import asyncio
import logging
import json
from nio import AsyncClient, RoomMessageText
from modules import check_email

# Load configuration from config.json
with open("config.json", "r") as config_file:
    config = json.load(config_file)
MATRIX_SERVER = config["MATRIX_SERVER"]
USERNAME = config["USERNAME"]
PASSWORD = config["PASSWORD"]

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def message_callback(room, event):
    try:
        if isinstance(event, RoomMessageText) and event.sender != client.user:
            message_content = event.body.strip()
            if message_content.startswith("!email "):
                email = message_content[len("!email "):].strip()
                logger.info(f"Checking email: {email}")
                
                result = await check_email(email)

                await client.room_send(
                    room_id=room.room_id,
                    message_type="m.room.message",
                    content={
                        "msgtype": "m.text",
                        "body": result,  # Plain text fallback
                        "format": "org.matrix.custom.html",
                        "formatted_body": result,  # HTML content
                    },
                )
    except Exception as e:
        logger.error(f"Error processing message: {e}")

async def main():
    global client
    client = AsyncClient(MATRIX_SERVER, USERNAME)
    await client.login(PASSWORD)
    logger.info("Logged in successfully!")

    client.add_event_callback(message_callback, RoomMessageText)
    await client.sync_forever(timeout=30000)

if __name__ == "__main__":
    asyncio.run(main())
