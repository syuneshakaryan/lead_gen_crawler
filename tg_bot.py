# import nest_asyncio
# nest_asyncio.apply()

# import os

# import logging
# import io
# import concurrent.futures
# import asyncio

# import pandas as pd

# from telegram import Update, InputFile
# from telegram.ext import (
#     ApplicationBuilder,
#     CommandHandler,
#     MessageHandler,
#     ContextTypes,
#     filters,
# )

# from bot import find_by_rules  # email extraction logic
# from utils import is_valid_email, is_deliverable_email  # Email validation functions
# from crawler import fetch_html  # Used to check base HTML access

# from dotenv import load_dotenv

# nest_asyncio.apply()
# load_dotenv() # Configure logging: set our logger and reduce library chatter.

# logging.basicConfig(
#     format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
# )
# logger = logging.getLogger(__name__)

# # Reduce logs from external libraries.
# logging.getLogger("httpx").setLevel(logging.WARNING)
# logging.getLogger("telegram").setLevel(logging.WARNING)

# async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
#     await update.message.reply_text(
#         "Welcome! Send me a list of websites (one per line) and I will process "
#         "each to extract emails. You will receive an Excel file with Domain, Email, and Access info."
#     )

# def process_single_domain(domain: str, idx: int) -> dict:
#     domain = domain.strip()
#     if not domain.startswith("http"):
#         domain = "https://" + domain

#     print(f"[{idx}] Processing {domain}...")
#     base_html = fetch_html(domain)
#     if base_html is None:
#         access_flag = "DENIED"
#     else:
#         access_flag = ""  # No logging needed if access is OK.

#     if base_html is None:
#         valid_emails = []
#     else:
#         emails = find_by_rules(domain)
#         valid_emails = [email for email in emails if is_valid_email(email) and is_deliverable_email(email)]

#     return {"Domain": domain, "Valid List": valid_emails, "Access": access_flag}

# async def process_websites(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
#     text = update.message.text
#     websites = [line.strip() for line in text.splitlines() if line.strip()]
#     if not websites:
#         await update.message.reply_text("No websites provided.")
#         return

#     await update.message.reply_text(
#         f"Processing {len(websites)} website(s). This may take a few moments..."
#     )
#     results = []
#     with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
#         futures = {
#             executor.submit(process_single_domain, website, idx + 1): website
#             for idx, website in enumerate(websites)
#         }
#         for future in concurrent.futures.as_completed(futures):
#             try:
#                 res = future.result()
#                 results.append(res)
#             except Exception as e:
#                 # Log errors as state changes.
#                 logger.error(f"Error processing {futures[future]}: {e}")

#     # Build dataframe for Excel output.
#     rows = []
#     for res in results:
#         access = res.get("Access", "")
#         if res.get("Valid List"):
#             for email in res["Valid List"]:
#                 rows.append({"Domain": res["Domain"], "Email": email, "Access": access})
#         else:
#             rows.append({"Domain": res["Domain"], "Email": "", "Access": access})

#     df = pd.DataFrame(rows, columns=["Domain", "Email", "Access"])
    
#     # Write DataFrame to an Excel file in memory using xlsxwriter.
#     output = io.BytesIO()
#     with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
#         df.to_excel(writer, index=False, sheet_name="Results")
#         workbook  = writer.book
#         worksheet = writer.sheets["Results"]
#         (max_row, max_col) = df.shape
#         red_format = workbook.add_format({'font_color': 'red'})
#         worksheet.conditional_format(
#             f"C2:C{max_row+1}", 
#             {
#                 'type': 'cell',
#                 'criteria': 'equal to',
#                 'value': '"DENIED"',
#                 'format': red_format
#             }
#         )
#     output.seek(0)

#     await update.message.reply_document(
#         document=InputFile(output, filename="results.xlsx"),
#         caption="Here is your Excel file with Domain, Email, and Access info."
#     )

# async def main() -> None:
#     nest_asyncio.apply()
#     # Replace with actual token.
#     token = os.getenv("BOT_TOKEN")
#     application = ApplicationBuilder().token(token).build()

#     application.add_handler(CommandHandler("start", start))
#     application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, process_websites))

#     await application.run_polling()

# if __name__ == "__main__":
#     asyncio.run(main())

import os
import logging
import io
import concurrent.futures
import asyncio
import nest_asyncio
import pandas as pd
from dotenv import load_dotenv

from telegram import Update, InputFile
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    filters,
)

# Your custom module imports
from bot import find_by_rules  
from utils import is_valid_email, is_deliverable_email  
from crawler import fetch_html  

# 1. Initialize environment and nested loop support
load_dotenv()
nest_asyncio.apply()

# 2. Configure logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)
logging.getLogger("httpx").setLevel(logging.WARNING)
logging.getLogger("telegram").setLevel(logging.WARNING)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text(
        "Welcome! Send me a list of websites (one per line) and I will process "
        "each to extract emails. You will receive an Excel file with Domain, Email, and Access info."
    )

def process_single_domain(domain: str, idx: int) -> dict:
    domain = domain.strip()
    if not domain.startswith("http"):
        domain = "https://" + domain

    print(f"[{idx}] Processing {domain}...")
    base_html = fetch_html(domain)
    
    access_flag = "DENIED" if base_html is None else ""

    if base_html is None:
        valid_emails = []
    else:
        emails = find_by_rules(domain)
        valid_emails = [e for e in emails if is_valid_email(e) and is_deliverable_email(e)]

    return {"Domain": domain, "Valid List": valid_emails, "Access": access_flag}

async def process_websites(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    text = update.message.text
    websites = [line.strip() for line in text.splitlines() if line.strip()]
    
    if not websites:
        await update.message.reply_text("No websites provided.")
        return

    await update.message.reply_text(f"Processing {len(websites)} website(s)...")
    
    results = []
    # Using ThreadPoolExecutor because the crawler functions are likely synchronous (requests/bs4)
    with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
        loop = asyncio.get_event_loop()
        tasks = [
            loop.run_in_executor(executor, process_single_domain, site, i+1)
            for i, site in enumerate(websites)
        ]
        results = await asyncio.gather(*tasks)

    # Build dataframe
    rows = []
    for res in results:
        if res.get("Valid List"):
            for email in res["Valid List"]:
                rows.append({"Domain": res["Domain"], "Email": email, "Access": res["Access"]})
        else:
            rows.append({"Domain": res["Domain"], "Email": "", "Access": res["Access"]})

    df = pd.DataFrame(rows, columns=["Domain", "Email", "Access"])
    
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        df.to_excel(writer, index=False, sheet_name="Results")
        workbook  = writer.book
        worksheet = writer.sheets["Results"]
        red_format = workbook.add_format({'font_color': 'red'})
        worksheet.conditional_format(f"C2:C{len(df)+1}", 
            {'type': 'cell', 'criteria': 'equal to', 'value': '"DENIED"', 'format': red_format})
    
    output.seek(0)
    await update.message.reply_document(
        document=InputFile(output, filename="results.xlsx"),
        caption="Here are your results."
    )

async def main() -> None:
    token = os.getenv("BOT_TOKEN")
    if not token:
        logger.error("No BOT_TOKEN found in .env file!")
        return

    application = ApplicationBuilder().token(token).build()

    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, process_websites))

    # CRITICAL FIX: close_loop=False prevents the RuntimeError on Windows/Streamlit
    await application.run_polling(close_loop=False)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        pass