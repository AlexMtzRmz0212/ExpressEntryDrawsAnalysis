"""
====================================================================
Express Entry Draw Automation Script (automation.py) [GitHub Action]
====================================================================

This script automates the process of checking for new Canadian Express Entry (EE) 
draws, updating local data files, and sending email notifications.

It is designed to be executed as a standalone script, typically by a scheduled 
task or a CI/CD pipeline (like the accompanying GitHub Action).

Main Workflow:
1.  **Import Dependencies**: Imports the `ExpressEntryManager` from the `Draws` 
    module and `os` for environment variables.
2.  **Load Credentials**: Securely retrieves SMTP configuration (server, port, 
    user, password, and email addresses) from environment variables.
3.  **Validate Credentials**: Checks if all required SMTP variables are present. 
    If not, it raises a `ValueError`.
4.  **Initialize Manager**: Creates an instance of `ExpressEntryManager`.
5.  **Check for Updates**: Calls `m.check_data_freshness()` to compare the
    count of draws in the local data files against the count from the live API.
6.  **Process Updates (If new data is found)**:
    a. Logs a message indicating new data.
    b. Calls `m.update_data()` to fetch the new draw(s) and overwrite the
       local `EE.json` and `EE.csv` files.
    c. Calls `m.analyze_draws()` to regenerate the `analysis.json` file.
    d. Calls `m.get_latest_draws()` and `m.format_draw_info()` to prepare
       formatted details about the most recent draw for the email.
    e. Calls `m.send_email()` to send a notification with the draw details
       to the specified recipient (`SMTP_TO_EMAIL_TEST`).
7.  **Skip (If no new data is found)**:
    a. Logs a message indicating the data is already up-to-date and skips
       the update and email process.
8.  **Error Handling**: A top-level `try...except` block catches any exceptions
    during execution and prints the error to standard output.

Required Modules:
- `os`: (Standard Library) Used to access environment variables.
- `Draws.ExpressEntryManager`: The custom class responsible for all API
  interaction, data processing (using `pandas`), and email logic.

Required Environment Variables:
- `SMTP_SERVER`: The address of the SMTP server (e.g., "smtp.gmail.com").
- `SMTP_PORT`: The port for the SMTP server (e.g., 587 for TLS).
- `SMTP_USER`: The username for SMTP authentication (often the 'from' email).
- `SMTP_PASSWORD`: The password (or App Password) for SMTP authentication.
- `SMTP_FROM_EMAIL`: The email address to send notifications from.
- `SMTP_TO_EMAIL_TEST`: The recipient email address for the notification.

"""

from Draws import ExpressEntryManager
import os
try:
    # Get credentials from environment
    smtp_server = os.getenv("SMTP_SERVER")
    smtp_port = int(os.getenv("SMTP_PORT", 587))
    smtp_user = os.getenv("SMTP_USER")
    smtp_password = os.getenv("SMTP_PASSWORD")
    from_email = os.getenv("SMTP_FROM_EMAIL")
    to_email_test = os.getenv("SMTP_TO_EMAIL_TEST")

    if not all([smtp_server, smtp_port, smtp_user, smtp_password, from_email, to_email_test]):
        raise ValueError("Required SMTP environment variables are not set.")
    
    m = ExpressEntryManager()
    needs_update, existing_count, api_count = m.check_data_freshness()
    
    if needs_update:
        print(f'New data found ({api_count} > {existing_count}).')
        m.update_data()
        m.analyze_draws()
        latest, previous = m.get_latest_draws()
        number, datetime, name, size, crs, since, between = m.format_draw_info(latest, previous)
        m.send_email(
            subject=f"New Express Entry Draw #{number} - {name}",
            body=f"Draw Date: {datetime}\nType: {name}\nInvitations: {size}\nMinimum CRS: {crs}\nThis Draw happened: {since}\nDays Between Previous Draw: {between}",
            to_email=to_email_test,
            from_email=from_email,
            smtp_server=smtp_server,
            smtp_port=smtp_port,
            smtp_user=smtp_user,
            smtp_password=smtp_password
        )
    else:
        print(f'No new draws found ({api_count} = {existing_count}). Skipping email.')
except Exception as e:
    print(f"An error occurred: {e}")