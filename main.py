from fastapi import FastAPI
from pydantic import BaseModel
from typing import List
import agentql
from playwright.sync_api import sync_playwright
from concurrent.futures import ThreadPoolExecutor
import playwright
playwright.install()

app = FastAPI()

class InfluencerMessage(BaseModel):
    INSTAGRAM_COOKIES : List[dict]
    influencers: List[str]
    messages: List[str]  # Now messages is a list corresponding to influencers

    def __init__(self, **data):
        super().__init__(**data)
        if len(self.influencers) != len(self.messages):
            raise ValueError("Number of influencers must match number of messages")

def message_influencer(INSTAGRAM_COOKIES,influencer: str, message: str):
    try:
        with sync_playwright() as playwright, playwright.chromium.launch(headless=True) as browser:
            context = browser.new_context()
            context.add_cookies(INSTAGRAM_COOKIES)  # Your existing cookies list
            
            page = agentql.wrap(context.new_page())
            page.goto("https://www.instagram.com")
            page.wait_for_timeout(2000)

            # Search for influencer
            search_button = page.get_by_prompt("search button which looks like a magnifying glass")
            search_button.click()
            page.wait_for_timeout(2000)

            search_input = page.get_by_prompt("search input field")
            search_input.click()
            page.wait_for_timeout(2000)
            search_input.fill(influencer)
            page.wait_for_timeout(2000)

            first_result = page.get_by_prompt("click on name of result in the search results")
            first_result.click()
            page.wait_for_timeout(2000)

            messages_button = page.get_by_prompt("message button for the person of the page i want to message")
            messages_button.click()
            page.wait_for_timeout(2000)

            try:
                not_now_button = page.get_by_prompt("not now button")
                not_now_button.click()
                page.wait_for_timeout(2000)
            except:
                pass

            message_input = page.get_by_prompt(f"message input field for {influencer}")
            message_input.click()
            page.wait_for_timeout(2000)
            message_input.fill(message)
            page.wait_for_timeout(2000)

            send_button = page.get_by_prompt("send button")
            send_button.click()
            page.wait_for_timeout(2000)

            return {"status": "success", "influencer": influencer, "message": message}
    except Exception as e:
        return {"status": "error", "influencer": influencer, "message": message, "error": str(e)}

@app.post("/send-messages")
async def send_messages(data: InfluencerMessage):
    results = []
    
    # Create a thread pool to handle multiple messages concurrently
    with ThreadPoolExecutor(max_workers=3) as executor:
        # Zip influencers and messages together for processing
        futures = [
            executor.submit(message_influencer,data.INSTAGRAM_COOKIES ,influencer, message)
            for influencer, message in zip(data.influencers, data.messages)
        ]
        
        for future in futures:
            results.append(future.result())
    
    return {
        "message": "Messages processing completed",
        "results": results
    }

