import asyncio
import logging
import json
import re
import subprocess
from nio import AsyncClient, RoomMessageText

# Load configuration from config.json
with open("config.json", "r") as config_file:
    config = json.load(config_file)
MATRIX_SERVER = config["MATRIX_SERVER"]
USERNAME = config["USERNAME"]
PASSWORD = config["PASSWORD"]

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def is_valid_email(email):
    """
    Validate email format using a regex.
    """
    email_regex = r'^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$'
    return re.match(email_regex, email) is not None

def parse_holehe_output(output: str, query: str) -> str:
    """
    Parse the output of Holehe to extract relevant results.
    """
    lines = output.splitlines()
    results = []
    additional_info = []

    for line in lines:
        # Stop parsing if "Email used" legend is encountered
        if line.strip().startswith("[+] Email used"):
            break

        # Match lines with "[+]" indicating a positive result
        if line.startswith("[+]"):
            parts = line.split(" ", 1)
            if len(parts) == 2:
                site = parts[1].strip()
                # Extract additional info (if available)
                if "/" in site:
                    site, *info = site.split(" / ")
                    title = info[0].strip()  # Extract the title (e.g., "FullName")
                    link = info[-1].strip()  # Extract the link
                    additional_info.append(f'<li><b>{title}:</b> <a href="{link}" target="_blank">{link}</a></li>')
                else:
                    url = f"https://{site}"
                    results.append(f'<li><a href="{url}" target="_blank">{site.capitalize()}</a></li>')

    # Format additional information and main results
    additional_info_section = (
        f"<h3>Information on {query}:</h3>"
        f"<ul>{''.join(additional_info)}</ul>" if additional_info else ""
    )
    main_results_section = (
        f"<h3>{query} registered at the following sites:</h3>"
        f"<ul>{''.join(results)}</ul>" if results else f"No results found for {query}."
    )

    return f"{additional_info_section}<br>{main_results_section}"

async def check_email(email: str) -> str:
    """
    Run the Holehe CLI tool for the given email and parse the output.
    """
    try:
        logging.info(f"Running Holehe CLI for email: {email}")
        process = subprocess.run(
            ["holehe", email],
            capture_output=True,
            text=True,
            check=True
        )
        # Get only stdout (strip progress bar updates from stderr if needed)
        raw_output = process.stdout
        logging.info(f"Raw output:\n{raw_output}")
        return parse_holehe_output(raw_output, email)
    except subprocess.CalledProcessError as e:
        logging.error(f"Holehe error: {e.stderr}")
        return "An error occurred while checking the email."
    except Exception as e:
        logging.error(f"Unexpected error in check_email: {e}")
        return "An unexpected error occurred."

async def message_callback(room, event):
    try:
        if isinstance(event, RoomMessageText) and event.sender != client.user:
            message_content = event.body.strip()
            if message_content.startswith("!email "):
                email = message_content[len("!email "):].strip()
                logger.info(f"Received query for email: {email}")

                # Validate email format before proceeding
                if not is_valid_email(email):
                    logger.warning(f"Invalid email format: {email}")
                    response = "The provided input is not a valid email format. Please try again with a valid email."
                    await client.room_send(
                        room_id=room.room_id,
                        message_type="m.room.message",
                        content={
                            "msgtype": "m.text",
                            "body": response,
                        },
                    )
                    return  # Exit early if email is invalid

                # Process the valid email query
                result = await check_email(email)
                response_html = (
                    f"{result}\n\n"
                    f"Finished report on {email} for {event.sender}."
                )
                plain_result = re.sub(r'<[^>]+>', '', result)  # Remove HTML tags for plain text
                plain_response = (
                    f"{plain_result}\n\n"
                    f"Finished report on {email} for {event.sender}."
                )

                await client.room_send(
                    room_id=room.room_id,
                    message_type="m.room.message",
                    content={
                        "msgtype": "m.text",
                        "body": plain_response,  # Plain text with URL for previews
                        "format": "org.matrix.custom.html",
                        "formatted_body": response_html,  # HTML content
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
