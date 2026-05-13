import random
import time
import logging
from telegram import Update
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, ConversationHandler, CallbackContext
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
from selenium_stealth import stealth
import random
import time

# Bot Configuration
TOKEN = '8211151893:AAEEF4JwQc6xBGUPFsS_O_2H2WIH0Q5c9YI'

# Conversation States
GET_EMAIL, GET_OTP = range(2)

def start(update: Update, context: CallbackContext) -> int:
    update.message.reply_text(
        "👋 Welcome to Instagram Account Creator Bot!\n\n"
        "Please send me the **Gmail address** you want to use for registration."
    )
    return GET_EMAIL

def get_email(update: Update, context: CallbackContext) -> int:
    email = update.message.text
    if '@' not in email:
        update.message.reply_text("❌ Please provide a valid email address.")
        return GET_EMAIL

    context.user_data['email'] = email
    
    # Generate random credentials
    username = f"user_{random.randint(100000, 999999)}"
    password = f"Pass_{random.randint(1000, 9999)}!@#"
    context.user_data['username'] = username
    context.user_data['password'] = password

    update.message.reply_text(
        f"🚀 **Starting Registration Process**\n\n"
        f"📧 Email: `{email}`\n"
        f"👤 Username: `{username}`\n"
        f"🔑 Password: `{password}`\n\n"
        "Please wait... I am filling the Instagram signup form."
    )

    try:
        # Setup Selenium with enhanced anti-detection
        chrome_options = Options()
        chrome_options.add_argument("--disable-blink-features=AutomationControlled")
        chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
        chrome_options.add_experimental_option('useAutomationExtension', False)
        
        # HEADLESS MODE (Required for Internet Servers)
        chrome_options.add_argument("--headless=new") 
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        
        chrome_options.add_argument("--window-size=1920,1080")
        chrome_options.add_argument("--lang=en-US")
        # Binary location for Linux servers
        import os
        if os.path.exists("/usr/bin/google-chrome"):
            chrome_options.binary_location = "/usr/bin/google-chrome"
        # Add a real User-Agent
        chrome_options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")

        driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)
        
        # Apply stealth settings
        stealth(driver,
            languages=["en-US", "en"],
            vendor="Google Inc.",
            platform="Win32",
            webgl_vendor="Intel Inc.",
            renderer="Intel Iris OpenGL Engine",
            fix_hairline=True,
        )
        
        context.user_data['driver'] = driver
        
        driver.get('https://www.instagram.com/accounts/emailsignup/')
        wait = WebDriverWait(driver, 30)

        # Handle Cookie Consent if it appears
        try:
            cookie_btn = wait.until(EC.element_to_be_clickable((By.XPATH, "//button[contains(text(), 'Allow all cookies') or contains(text(), 'Decline optional cookies')]")))
            cookie_btn.click()
            time.sleep(1)
        except:
            pass

        # Fill the signup form
        email_field = wait.until(EC.presence_of_element_located((By.NAME, "emailOrPhone")))
        time.sleep(random.uniform(1, 3)) # Human-like delay
        email_field.send_keys(email)
        
        driver.find_element(By.NAME, "fullName").send_keys("Automated User")
        driver.find_element(By.NAME, "username").send_keys(username)
        driver.find_element(By.NAME, "password").send_keys(password)
        
        time.sleep(random.uniform(1, 2))
        
        # Click Sign Up button
        signup_button = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, "button[type='submit']")))
        signup_button.click()
        
        # Handle Birthday Step (Instagram usually requires this)
        update.message.reply_text("🎂 Handling birthday step...")
        time.sleep(3)
        
        try:
            # Check if birthday selection is present
            month_select = wait.until(EC.presence_of_element_located((By.XPATH, "//select[@title='Month']")))
            month_select.send_keys("January")
            driver.find_element(By.XPATH, "//select[@title='Day']").send_keys("1")
            driver.find_element(By.XPATH, "//select[@title='Year']").send_keys("1995")
            
            # Click Next after birthday
            next_btns = driver.find_elements(By.XPATH, "//button[contains(text(), 'Next')]")
            if next_btns:
                next_btns[0].click()
            else:
                # Fallback to general button search if text match fails
                driver.find_element(By.CSS_SELECTOR, "button._acan").click()
        except Exception as bday_err:
            print(f"Birthday step skipped or error: {bday_err}")

        update.message.reply_text(
            "✅ Form submitted!\n\n"
            "📨 **Now, please check your email and send me the 6-digit OTP (Verification Code).**"
        )
        return GET_OTP

    except Exception as e:
        update.message.reply_text(f"❌ An error occurred during form filling: {str(e)}")
        if 'driver' in context.user_data:
            context.user_data['driver'].quit()
        return ConversationHandler.END

def get_otp(update: Update, context: CallbackContext) -> int:
    otp = update.message.text
    driver = context.user_data.get('driver')

    if not driver:
        update.message.reply_text("❌ Session lost. Please type /start to try again.")
        return ConversationHandler.END

    try:
        update.message.reply_text("⏳ Verifying OTP...")
        wait = WebDriverWait(driver, 30)
        
        # Find OTP field
        otp_field = wait.until(EC.presence_of_element_located((By.NAME, "email_confirmation_code")))
        otp_field.send_keys(otp)
        
        time.sleep(1)
        
        # Click Next/Confirm
        confirm_button = wait.until(EC.element_to_be_clickable((By.XPATH, "//button[contains(text(), 'Next')]")))
        confirm_button.click()
        
        time.sleep(10) # Wait for Instagram to process the account creation
        
        update.message.reply_text(
            "🎉 **Account Created Successfully!**\n\n"
            f"👤 Username: `{context.user_data['username']}`\n"
            f"🔑 Password: `{context.user_data['password']}`\n\n"
            "Browser session closed."
        )
        
    except Exception as e:
        update.message.reply_text(f"❌ Failed to verify OTP: {str(e)}")
    finally:
        driver.quit()
        context.user_data.clear()

    return ConversationHandler.END

def cancel(update: Update, context: CallbackContext) -> int:
    update.message.reply_text("❌ Registration cancelled.")
    if 'driver' in context.user_data:
        context.user_data['driver'].quit()
    context.user_data.clear()
    return ConversationHandler.END

def main():
    updater = Updater(TOKEN, use_context=True)
    dp = updater.dispatcher

    conv_handler = ConversationHandler(
        entry_points=[CommandHandler('start', start)],
        states={
            GET_EMAIL: [MessageHandler(Filters.text & ~Filters.command, get_email)],
            GET_OTP: [MessageHandler(Filters.text & ~Filters.command, get_otp)],
        },
        fallbacks=[CommandHandler('cancel', cancel)],
    )

    dp.add_handler(conv_handler)

    print("Bot is running...")
    updater.start_polling()
    updater.idle()

if __name__ == '__main__':
    main()
