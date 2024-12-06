import subprocess
import logging


async def check_email(email):
    """
    Check the given email using the Holehe CLI tool.

    Args:
        email (str): The email address to check.

    Returns:
        str: The parsed results from Holehe or an error message.
    """
    logging.info(f"Running Holehe CLI for email: {email}")
    
    try:
        # Run the Holehe CLI command
        process = subprocess.run(
            ["holehe", email],
            capture_output=True,
            text=True
        )
        
        stdout = process.stdout.strip()
        stderr = process.stderr.strip()

        # Log stderr if it contains any output
        if stderr:
            logging.warning(f"Holehe CLI stderr: {stderr}")

        # If stdout is empty, log and return an error
        if not stdout:
            logging.error(f"Holehe CLI returned no output for {email}.")
            return "No results found for the email."

        # Refined parsing logic
        results_lines = []
        is_relevant_section = False

        for line in stdout.splitlines():
            # Skip progress bar
            if "100%|##########|" in line:
                continue

            # Detect the start of the results section
            if line.startswith("*******************"):
                is_relevant_section = True
                continue

            # Collect relevant lines in the results section
            if is_relevant_section:
                if line.strip().startswith("[+]"):  # Only include relevant positive results
                    results_lines.append(line.strip())

        # Combine and format results
        if results_lines:
            results = "\n".join(results_lines)
            logging.debug(f"Parsed results for {email}:\n{results}")
            return results
        else:
            logging.info(f"No relevant data found for {email}.")
            return "No results found for the email."

    except Exception as e:
        logging.error(f"Error while running Holehe: {e}")
        return "An error occurred while checking the email. Please try again later."
