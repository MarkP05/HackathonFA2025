from google import genai
import os

# --- 1. Read API Key from File ---
try:
    with open("api_key.txt", "r") as f:
        # .strip() removes any leading/trailing whitespace or newline characters
        api_key = f.read().strip() 
except FileNotFoundError:
    print("Error: 'api_key.txt' not found.")
    # You might want to exit the script here if the key is mandatory
    exit() 
except Exception as e:
    print(f"An error occurred while reading the file: {e}")
    exit()

# --- 2. Initialize Client with File Key ---
if not api_key:
    print("Error: 'api_key.txt' is empty. Please ensure the key is on the first line.")
    exit()
    
# Initialize the client by passing the key read from the file
client = genai.Client(api_key=api_key)

# --- 3. Make the API Call ---
response = client.models.generate_content(
    model = "gemini-2.0-flash",
    contents = "Why is the grass green?"
)

print(response)