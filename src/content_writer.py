import os
import google.generativeai as genai
from dotenv import load_dotenv
from google.generativeai.types import GenerationConfig

load_dotenv()

SYSTEM_PROMPT = """
你係我嘅好朋友，專門幫我留意 Black Friday 減價。你係香港人

你係一個睇人買野最開心既人。

如果我問「寫 email 標題」，請你幫我寫一個簡短、有吸引力但唔似廣告嘅 標題。

語氣要鳩鳩地、開心，好似 share 好消息咁，但需要朋友借d2推銷。

請直接回覆成品，不要解釋。
"""

NEGATIVE_PROMPT = """
寫 email 標題  寫今日無野減價
ONLY OUTPUT THE TITLE, NO ADDITIONAL TEXT, NO EMOJIS
"""

POSITIVE_PROMPT = """
寫 email 標題  以下係今日減價嘅野，推朋友落坑買：
今日要買既野： {summary}
ONLY OUTPUT THE TITLE, NO ADDITIONAL TEXT, NO EMOJIS  
"""

POSITIVE_OPENING_PROMPT = """
幫我寫封email開頭，1-2句，用鳩鳩又開心嘅語氣講, 好似分享好消息咁，內容要包含 {summary}，並幫手推銷
"""

NEGATIVE_OPENING_PROMPT = """
幫我寫封email開頭，20字內，用鳩鳩語氣講今日無減價，好慘冇得買。
"""

gen_config = GenerationConfig(
    temperature=1.0,
    top_p=0.9,
    top_k=40,
    max_output_tokens=2000,
)

class ContentWriter:
    def __init__(self):
        self.OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
        if not self.OPENAI_API_KEY:
            print("❌ OPENAI_API_KEY is not set in environment variables.")
        else:
            self.no_api_key = False
        try:
            genai.configure(api_key=self.OPENAI_API_KEY)
            self.model = genai.GenerativeModel(
            model_name="gemini-2.5-flash",
            system_instruction=SYSTEM_PROMPT,
            generation_config=gen_config
        )
        except Exception as e:
            print("❌ Gemini service test failed:", e)

    def write_title(self, type: str, summary: list[dict[str, str]]) -> str:
        prompt_map = {
            "positive": POSITIVE_PROMPT,
            "negative": NEGATIVE_PROMPT
        }
        prompt = prompt_map.get(type)
        if not prompt:
            raise ValueError(f"Invalid type: {type}")
        
        if type == "positive":
            summary = ", ".join([f"Wishlisted by {item['owner']} {item['product_id']} at ${item['best_price']}" for item in summary])

        prompt = prompt.format(summary=summary)
        try:
            print("📝 Generating title with prompt:", prompt)
            response = self.model.generate_content(prompt)
            if response.candidates and response.candidates[0].content.parts:
                return response.text
            else:
                print("⚠️ No valid content returned. Finish reason:", response)
                return ""
        except Exception as e:
            print("❌ Error occurred while generating title:", e)
            return "Error"
    
    def write_opening(self, type:str, summary: list[dict[str,str]]) -> str:
        if type == "summary": return ""
        
        prompt_map = {
            "positive": POSITIVE_OPENING_PROMPT,
            "negative": NEGATIVE_OPENING_PROMPT
        }
        prompt = prompt_map.get(type)
        if not prompt:
            raise ValueError(f"Invalid type: {type}")
        
        if type == "positive":
            summary = ", ".join([f"Wishlisted by {item['owner']} {item['product_id']} at ${item['best_price']}" for item in summary])
            
        prompt = prompt.format(summary=summary)
        try:
            print("📝 Generating opening with prompt:", prompt)
            response = self.model.generate_content(prompt)
            if response.candidates and response.candidates[0].content.parts:
                return response.text
            else:
                print("⚠️ No valid content returned. Finish reason:", response)
                return "係時候買野。" if type == "positive" else "無野買。"
        except Exception as e:
            print("❌ Error occurred while generating opening:", e)
            return "係時候買野。" if type == "positive" else "無野買。"

if __name__ == "__main__":
    writer = ContentWriter()
    output = writer.write_title(type="negative")
    print(output)