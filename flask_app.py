import os
import json
import requests
from flask import Flask, request, jsonify, render_template

app = Flask(__name__)

# Replace with your actual Gemini API Key
API_KEY = ""

# This route serves the HTML page
@app.route("/", methods=["GET"])
def home():
    return render_template("index.html")

# This route handles the API requests from the frontend
@app.route("/generate", methods=["POST"])
def generate():
    data = request.get_json(silent=True) or {}
    user_ingredients = data.get("ingredients", "")

    # Define the system prompt for the Gemini model
    system_prompt = f"""
    คุณคือ AI นักชิมอาหารระดับปรมาจารย์ (Master Taster) ในเกมทำอาหาร
    หน้าที่ของคุณคือการประเมิน 'เมนูทดลอง' ที่ผู้ใช้ปรุงขึ้นโดยการระบุวัตถุดิบและ 'ปริมาณ' มาให้

    คุณต้องทำตามขั้นตอนต่อไปนี้อย่างเคร่งครัด:
    1.  **วิเคราะห์วัตถุดิบและสัดส่วน:**
        * พยายามคาดเดาว่าผู้ใช้กำลังจะทำเมนูอะไร (เช่น วัตถุดิบมี มะละกอ, พริก, มะนาว, น้ำปลา -> น่าจะเป็นส้มตำ)
        * วิเคราะห์ 'ปริมาณ' ของวัตถุดิบแต่ละอย่าง เทียบกับสูตรมาตรฐานของเมนูนั้นๆ

    2.  **ตัดสินรสชาติ:**
        * **ถ้าสัดส่วนสมบูรณ์แบบ:** รสชาติจะ 'อร่อย' และ 'กลมกล่อม'
        * **ถ้าสัดส่วนไม่สมดุล:** รสชาติจะ 'ไม่อร่อย' ให้ระบุสาเหตุให้ชัดเจน เช่น เค็มเกินไป (เพราะน้ำปลาเยอะ), เผ็ดจนทานไม่ได้ (เพราะพริกเยอะ), จืดชืด (เพราะขาดเครื่องปรุงหลัก) หรือเปรี้ยวเกินไป

    3.  **สร้างผลลัพธ์ในรูปแบบ JSON:**
        * **dish_name:** ตั้งชื่อเมนูตามที่คาดเดา หรือตั้งชื่อแบบสร้างสรรค์ที่สะท้อนถึงรสชาติที่ได้ชิม เช่น "ส้มตำรสจัดจ้าน" หากอร่อย หรือ "ยำทะเลเค็มบาดคอ" หากเค็มเกินไป
        * **ingredients:** ระบุวัตถุดิบและปริมาณทั้งหมดที่ผู้ใช้ป้อนเข้ามา
        * **customer_review:** เขียนคำวิจารณ์ในฐานะนักชิม ต้องตรงไปตรงมา บอกเหตุผลว่าทำไมถึงอร่อยหรือไม่่อย่อย และถ้าไม่อร่อยควรมีคำแนะนำสั้นๆ เพื่อปรับปรุง

    ตอบกลับในรูปแบบ JSON เท่านั้น โดยมีโครงสร้างดังนี้:
    {{
        "dish_name": "ชื่อเมนู",
        "ingredients": ["วัตถุดิบ1", "วัตถุดิบ2", ...],
        "customer_review": "รีวิวจากนักชิม"
    }}
    """

    # Prepare the request payload for Gemini API
    payload = {
        "contents": [
            {
                "parts": [{"text": user_ingredients}]
            }
        ],
        "systemInstruction": {
            "parts": [{"text": system_prompt}]
        },
        "generationConfig": {
            "responseMimeType": "application/json"
        }
    }

    # Check if API_KEY is set
    if not API_KEY:
        print("API Key is not set. Please set the GOOGLE_API_KEY environment variable.")
        return jsonify({"error": "API Key is not configured."}), 500

    api_url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash-preview-05-20:generateContent?key={API_KEY}"

    try:
        # Make the API call to Gemini
        response = requests.post(api_url, headers={'Content-Type': 'application/json'}, data=json.dumps(payload))
        response.raise_for_status()

        result = response.json()
        if result.get("candidates") and result["candidates"][0].get("content"):
            gemini_response = result["candidates"][0]["content"]["parts"][0]["text"]
            return jsonify(json.loads(gemini_response))
        else:
            return jsonify({"error": "ไม่สามารถสร้างเมนูได้ กรุณาลองอีกครั้ง"}), 500

    except requests.exceptions.RequestException as e:
        print(f"เกิดข้อผิดพลาดในการเชื่อมต่อกับ Gemini API: {e}")
        return jsonify({"error": "ไม่สามารถเชื่อมต่อกับบริการ AI ได้"}), 500
