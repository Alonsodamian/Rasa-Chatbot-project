import os
import pandas as pd
import openai
from typing import Any, Text, Dict, List
from rasa_sdk import Action, Tracker
from rasa_sdk.executor import CollectingDispatcher
from dotenv import load_dotenv


load_dotenv()

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

if not OPENAI_API_KEY:
    raise ValueError("API Key OpenAI tidak ditemukan. Setel variabel environment OPENAI_API_KEY.")


client = openai.OpenAI(api_key=OPENAI_API_KEY)


BASE_DIR = os.path.dirname(os.path.abspath(__file__))  # Cari path saat ini
CSV_PATH = os.path.join(BASE_DIR, "../dataset/data_produk.csv")  # Akses file dataset

class ActionCariProduk(Action):
    def name(self) -> Text:
        return "action_cari_produk"

    def run(self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:

        try:
            df = pd.read_csv(CSV_PATH)
            df["price"] = pd.to_numeric(df["price"], errors="coerce").fillna(0).astype(int)
        except Exception as e:
            dispatcher.utter_message(text="Terjadi kesalahan saat membaca database produk. Coba lagi nanti.")
            return []

        category = tracker.get_slot("category")
        price = tracker.get_slot("price")
        colour = tracker.get_slot("colour")
        shop_name = tracker.get_slot("shop_name")

        max_price = None
        if price:
            try:
                price = price.lower().replace(" juta", "000000").replace(" ribu", "000").replace(" di bawah ", "").replace("rp", "").replace(",", "").strip()
                max_price = int(price)
            except ValueError:
                dispatcher.utter_message(text="Maaf, saya tidak bisa memahami harga yang Anda berikan.")
                return []

        
        filtered_products = df.copy()

        if category:
            filtered_products = filtered_products[filtered_products["category"].str.contains(category, case=False, na=False)]
        if max_price is not None and max_price > 0:
            filtered_products = filtered_products[filtered_products["price"] <= max_price]
        if colour:
            filtered_products = filtered_products[filtered_products["colour"].str.contains(colour, case=False, na=False)]
        if shop_name:
            filtered_products = filtered_products[filtered_products["shop_name"].str.contains(shop_name, case=False, na=False)]

        if not filtered_products.empty:
            response = "Berikut beberapa produk yang cocok dengan pencarian Anda:\n"
            for _, product in filtered_products.head(5).iterrows():
                response += f"- **{product['item_name']}** | Warna: {product['colour']} | Harga: Rp{product['price']:,} | Brand: {product['shop_name']}\n"
        else:
            user_query = f"Cari produk kategori {category} dengan harga maksimal Rp{max_price:,} dan warna {colour} di toko {shop_name}."
            response = self.ask_gpt(user_query)

        dispatcher.utter_message(text=response)
        return []

    def ask_gpt(self, user_query: str) -> str:
        """Memanggil GPT-4o untuk memberikan rekomendasi atau jawaban."""
        try:
            completion = client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {"role": "system", "content": "Kamu adalah asisten chatbot yang membantu mencari produk e-commerce dan memberikan rekomendasi."},
                    {"role": "user", "content": user_query}
                ]
            )
            gpt_response = completion.choices[0].message.content
            return f"Saya tidak menemukan produk dalam database, tetapi berdasarkan pencarian saya:\n{gpt_response}"
        except Exception:
            return "Maaf, saat ini saya tidak bisa mengakses sistem pencarian produk AI. Coba lagi nanti."


class ActionGPTFallback(Action):
    def name(self) -> str:
        return "action_gpt_fallback"

    def run(self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict[str, Any]) -> List[Dict[str, Any]]:
        user_message = tracker.latest_message.get("text", "")

        try:
            response = client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {"role": "system", "content": "Anda adalah asisten chatbot e-commerce. Anda hanya menjawab pertanyaan yang berhubungan dengan produk, pembelian, pembayaran, pengiriman, dan layanan pelanggan."},
                    {"role": "user", "content": user_message}
                ]
            )
            reply = response.choices[0].message.content
        except Exception as e:
            reply = "Maaf, saya mengalami kesulitan memahami pertanyaan Anda."

        dispatcher.utter_message(text=reply)
        return []
