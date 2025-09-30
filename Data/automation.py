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