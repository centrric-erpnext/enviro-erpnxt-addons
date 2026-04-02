import frappe
from enviro.cron.recurring import execute_daily_operations

def execute():
    try:
        execute_daily_operations()
        print("Cron syntax runs flawlessly!")
    except Exception as e:
        print(f"Error: {str(e)}")
