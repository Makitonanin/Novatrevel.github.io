from flask import Flask, render_template, request, jsonify
from pathlib import Path
from datetime import datetime
import json
import re

app = Flask(__name__)
BASE_DIR = Path(__file__).resolve().parent
BOOKINGS_FILE = BASE_DIR / "bookings.json"

# Каталог туров — единый источник данных для API и формы бронирования.
TOURS = [
    {"id": "sulak", "title": "Сулакский каньон", "duration": "1 день", "price": 4500,
     "description": "Бирюзовая вода, головокружительные панорамы и прогулка на катере.",
     "tag": "Хит продаж", "image": "sulak.png"},

    {"id": "dagestan-3", "title": "Дагестан за 3 дня", "duration": "3 дня / 2 ночи", "price": 18900,
     "description": "Главные природные и исторические места республики в одном маршруте.",
     "tag": "Бестселлер", "image": "mountains.png"},

    {"id": "gamsutl", "title": "Гамсутль и Гуниб", "duration": "1 день", "price": 5900,
     "description": "Атмосфера аула-призрака, горные дороги и история Дагестана.",
     "tag": "Горы", "image": "gamsutl.png"},

    {"id": "derbent", "title": "Дербент — древний город", "duration": "1 день", "price": 3900,
     "description": "Крепость Нарын-Кала, старинные улочки и Каспийское побережье.",
     "image": "derbent.png"},

    {"id": "sarykum", "title": "Бархан Сарыкум", "duration": "4–5 часов", "price": 3200,
     "description": "Песчаные дюны среди гор и необычные пейзажи заповедника.",
     "tag": "Природа", "image": "sarykum.png"},
        {
        "id": "goor",
        "title": "Гоор и Язык тролля",
        "duration": "1 день",
        "price": 5000,
        "description": "Путешествие к древним башням аула Гоор, захватывающие виды на горы и знаменитый скальный выступ «Язык тролля».",
        "tag": "Горы",
        "image": "goor.png"
    },
    
         {
        "id": "chechnya",
        "title": "Чечня: Шали, Аргун и Грозный",
        "duration": "1 день",
        "price": 5500,
        "description": "Мечети Шали и Аргуна, знакомство с Грозным и культурой Чечни.",
        "tag": "Новинка",
        "image": "chechnya.png"
    },
    {
        "id": "hunzakh",
        "title": "Хунзах — Каменная чаша",
        "duration": "1 день",
        "price": 4500,
        "description": "Живописные горные пейзажи, водопады и загадочная Каменная чаша.",
        "tag": "Горы",
        "image": "hunzakh.png"
    },
        {
        "id": "saltinskoe",
        "title": "Салтинское ущелье и водопад",
        "duration": "1 день",
        "price": 4000,
        "description": "Прогулка по живописному Салтинскому ущелью и знакомство с уникальным подземным водопадом.",
        "tag": "Природа",
        "image": "saltinskoe.png"
    },


]

def load_bookings():
    """Читает заявки; при первом запуске возвращает пустой список."""
    if not BOOKINGS_FILE.exists():
        return []
    try:
        data = json.loads(BOOKINGS_FILE.read_text(encoding="utf-8"))
        return data if isinstance(data, list) else []
    except (json.JSONDecodeError, OSError):
        return []

@app.get("/")
def index():
    return render_template("index.html")

@app.get("/api/tours")
def api_tours():
    return jsonify({"tours": TOURS})

@app.post("/book")
def book():
    # Серверная проверка обязательна, даже если на странице есть JS-валидация.
    data = request.get_json(silent=True) or request.form.to_dict()
    name = str(data.get("name", "")).strip()
    phone = str(data.get("phone", "")).strip()
    tour_id = str(data.get("tour_id", "")).strip()
    date = str(data.get("date", "")).strip()
    people_raw = str(data.get("people", "")).strip()
    promo = str(data.get("promo", "")).strip()
    comment = str(data.get("comment", "")).strip()

    errors = {}
    if len(name) < 2:
        errors["name"] = "Укажите имя (не менее 2 символов)."
    digits = re.sub(r"\D", "", phone)
    if len(digits) not in (10, 11):
        errors["phone"] = "Укажите корректный номер телефона."
    if tour_id not in {tour["id"] for tour in TOURS}:
        errors["tour_id"] = "Выберите тур из списка."
    try:
        people = int(people_raw)
        if not 1 <= people <= 20:
            raise ValueError
    except (TypeError, ValueError):
        people = 0
        errors["people"] = "Количество человек должно быть от 1 до 20."
    try:
        selected_date = datetime.strptime(date, "%Y-%m-%d").date()
        if selected_date < datetime.now().date():
            errors["date"] = "Дата не может быть в прошлом."
    except ValueError:
        errors["date"] = "Укажите дату поездки."

    if errors:
        return jsonify({"ok": False, "message": "Проверьте заполнение формы.", "errors": errors}), 400

    selected_tour = next(tour for tour in TOURS if tour["id"] == tour_id)
    booking = {
        "id": datetime.now().strftime("%Y%m%d%H%M%S%f"),
        "created_at": datetime.now().isoformat(timespec="seconds"),
        "name": name, "phone": phone, "tour_id": tour_id,
        "tour_title": selected_tour["title"], "date": date,
        "people": people, "promo": promo, "comment": comment
    }
    bookings = load_bookings()
    bookings.append(booking)
    try:
        BOOKINGS_FILE.write_text(
            json.dumps(bookings, ensure_ascii=False, indent=2), encoding="utf-8"
        )
    except OSError:
        app.logger.exception("Не удалось сохранить заявку")
        return jsonify({"ok": False, "message": "Не удалось сохранить заявку. Попробуйте позже."}), 500

    return jsonify({
        "ok": True,
        "message": "Мы свяжемся с вами в ближайшее время.",
        "booking_id": booking["id"]
    }), 201

if __name__ == "__main__":
    # debug=True удобно при локальной разработке; для публикации отключите debug.
    app.run(host="127.0.0.1", port=5000, debug=True)
