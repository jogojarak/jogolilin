from playwright.sync_api import Playwright, sync_playwright
import time
from datetime import datetime
import pytz
import requests
import os
import re

from dotenv import load_dotenv
load_dotenv()

userid = os.getenv("userid")
pw = os.getenv("pw")
telegram_token = os.getenv("TELEGRAM_TOKEN")
telegram_chat_id = os.getenv("TELEGRAM_CHAT_ID")

wib = datetime.now(pytz.timezone("Asia/Jakarta")).strftime("%Y-%m-%d %H:%M WIB")

def log_status(emoji: str, message: str):
    print(f"{emoji} {message}")

def baca_file(file_name: str) -> str:
    with open(file_name, 'r') as file:
        return file.read().strip()

def kirim_telegram_log(status: str, pesan: str):
    log_text = pesan
    print(log_text)
    if telegram_token and telegram_chat_id:
        try:
            response = requests.post(
                f"https://api.telegram.org/bot{telegram_token}/sendMessage",
                data={
                    "chat_id": telegram_chat_id,
                    "text": log_text,
                    "parse_mode": "Markdown"
                }
            )
            if response.status_code != 200:
                print(f"Gagal kirim ke Telegram. Status: {response.status_code}")
                print(f"Respon Telegram: {response.text}")
        except Exception as e:
            print("Error saat mengirim ke Telegram:", e)
    else:
        print("Token atau chat_id tidak tersedia.")

def parse_nomorbet(nomorbet: str):
    try:
        kombinasi, nominal = nomorbet.split('#')
        jumlah_kombinasi = len(kombinasi.split('*'))
        return jumlah_kombinasi, nominal
    except:
        return 0, "0"

def run(playwright: Playwright) -> None:
    try:
        log_status("📂", "Membaca file nomorbet...")
        nomorbet = baca_file("nomorbet.txt")
        jumlah_kombinasi, bet = parse_nomorbet(nomorbet)
        log_status("📬", f"Nomor ditemukan: {nomorbet}")

        log_status("🌐", "Membuka browser dan login...")
        browser = playwright.chromium.launch(headless=True)
        context = browser.new_context(**playwright.devices["Pixel 7"])
        page = context.new_page()

        page.goto("https://indratogel31303.com/lite")
        page.locator("#entered_login").fill(userid)
        page.locator("#entered_password").fill(pw)
        page.get_by_role("button", name="Login").click()

        log_status("🔐", "Login berhasil, masuk ke menu Pools > HOKIDRAW > 4D Classic")
        page.get_by_role("link", name="Pools").click()
        page.get_by_role("link", name="HOKIDRAW").click()
        time.sleep(2)
        page.get_by_role("button", name="4D Classic").click()
        time.sleep(2)

        log_status("🧾", "Mengisi form taruhan...")
        page.get_by_role("cell", name="BET FULL").click()
        page.locator("#tebak").fill(nomorbet)
        page.once("dialog", lambda dialog: dialog.accept())

        log_status("📨", "Mengirim taruhan...")
        page.get_by_role("button", name="KIRIM").click()

        log_status("⏳", "Menunggu konfirmasi dari sistem...")

# Ambil saldo dulu
        try:
            saldo = page.locator("#bal-text").inner_text()
        except Exception as e:
            saldo = "tidak diketahui"
            print("⚠️ Gagal ambil saldo:", e)

        try:
            page.wait_for_selector("text=Bet Sukses!!", timeout=15000)

            pesan_sukses = (
                "[SUKSES]\n"
                f"🎯 {jumlah_kombinasi} kombinasi\n"
                f"💸 Rp. {bet}\n"
                f"💰 Rp. {saldo}\n"
                f"⌚ {wib}"
            )
            log_status("✅", pesan_sukses)
            kirim_telegram_log("SUKSES", pesan_sukses)
        except:
            log_status("❌", "Gagal: Teks 'Bet Sukses!!' tidak ditemukan.")
            kirim_telegram_log("GAGAL", f"[GAGAL]\n❌💰 Rp. {saldo}\n⌚ {wib}")


        context.close()
        browser.close()
    except Exception as e:
        log_status("❌", "Terjadi kesalahan saat menjalankan script.")
        print("Detail error:", e)
        kirim_telegram_log("GAGAL", f"[GAGAL]\n❌ Error: {str(e)}")

with sync_playwright() as playwright:
    run(playwright)
