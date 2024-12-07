import subprocess
import logging

logging.basicConfig(level=logging.INFO)

def parse_holehe_output(output: str) -> str:
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
                    additional_info.append(f'<a href="{info[-1].strip()}" target="_blank">{info[-1].strip()}</a>')
                # Create formatted result
                url = f"https://{site}"
                results.append(f'<li><a href="{url}" target="_blank">{site.capitalize()}</a></li>')

    # Format results and additional info
    result_message = (
        "<h3>Email registered at the following sites:</h3>"
        f"<ul>{''.join(results)}</ul>"
    )
    if additional_info:
        result_message += (
            "<br><b>Additional Information:</b><br>"
            f"<ul>{''.join(f'<li>{info}</li>' for info in additional_info)}</ul>"
        )

    return result_message if results else "No results found for the email."

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
        return parse_holehe_output(raw_output)
    except subprocess.CalledProcessError as e:
        logging.error(f"Holehe error: {e.stderr}")
        return "An error occurred while checking the email."
    except Exception as e:
        logging.error(f"Unexpected error in check_email: {e}")
        return "An unexpected error occurred."
