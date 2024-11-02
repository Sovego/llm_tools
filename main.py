import json
import asyncio
import ollama_tools
import requests
import logging
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
EMAIL_ADDRESS = "example@example.com"
EMAIL_PASSWORD = "password_here"
SMTP_SERVER = "smtp.gmail.com"  
SMTP_PORT = 587  


logging.basicConfig(level=logging.DEBUG)
def calculate_expression(expression: str) -> str:
    try:
        result = eval(expression)
        logging.debug(f"Результат вычисления: {result}")
        return json.dumps({"result": result})
    except Exception as e:
        logging.error(f"Ошибка в вычислениях: {str(e)}")
        return json.dumps({"error": f"Ошибка в вычислениях: {str(e)}"})

def get_coordinates(city: str) -> dict:
    try:
        url = f"http://api.openweathermap.org/geo/1.0/direct?q={city}&limit=1&appid=011af1a27c922a7a7385ecba5809ecb4"
        response = requests.get(url)
        data = response.json()
        
        if response.status_code == 200 and data:
            logging.debug(f"Coordinates for {city}: {data[0]['lat']}, {data[0]['lon']}")
            return {"lat": data[0]["lat"], "lon": data[0]["lon"]}
        else:
            logging.error(f"Не удалось получить координаты для города {city}.")
            return {"error": f"Не удалось получить координаты для города {city}."}
    except Exception as e:
        logging.error(f"Ошибка при запросе к Geocoding API: {str(e)}")
        return {"error": f"Ошибка при запросе к Geocoding API: {str(e)}"}

def get_weather(city: str) -> str:
    coordinates = get_coordinates(city)
    if "error" in coordinates:
        return json.dumps(coordinates)

    lat = coordinates["lat"]
    lon = coordinates["lon"]
    
    try:
        url = f"http://api.openweathermap.org/data/2.5/weather?lat={lat}&lon={lon}&appid=011af1a27c922a7a7385ecba5809ecb4&units=metric&lang=ru"
        response = requests.get(url)
        weather_data = response.json()

        if response.status_code == 200:
            description = weather_data['weather'][0]['description']
            temperature = weather_data['main']['temp']
            feels_like = weather_data['main']['feels_like']
            humidity = weather_data['main']['humidity']
            result = {
                "city": city,
                "description": description,
                "temperature": f"{temperature}°C",
                "feels_like": f"{feels_like}°C",
                "humidity": f"{humidity}%",
            }
            return json.dumps(result)
        else:
            logging.error(f"Не удалось получить данные о погоде для города {city}.")
            return json.dumps({"error": f"Не удалось получить данные о погоде для города {city}."})
    except Exception as e:
        logging.error(f"Ошибка при запросе к Weather API: {str(e)}")
        return json.dumps({"error": f"Ошибка при запросе к Weather API: {str(e)}"})


def send_email(recipient: str, subject: str, message: str) -> str:
    try:
        msg = MIMEMultipart()
        msg["From"] = EMAIL_ADDRESS
        msg["To"] = recipient
        msg["Subject"] = subject
        msg.attach(MIMEText(message, "plain"))

        server = smtplib.SMTP(SMTP_SERVER, SMTP_PORT)
        server.starttls()  
        server.login(EMAIL_ADDRESS, EMAIL_PASSWORD)
        
        server.send_message(msg)
        server.quit()
        logging.debug("Сообщение отправлено.")
        return "Сообщение успешно отправлено."
    except Exception as e:
        logging.error(f"Ошибка при отправке сообщения: {str(e)}")
        return f"Ошибка при отправке сообщения: {str(e)}"

# Функция чата
async def chat():
    wrapper = ollama_tools.OllamaWrapper('llama3-groq-tool-use')
    wrapper.add_tool(
    name="send_email",
    func=send_email,
    description="Отправляет электронное письмо на указанный адрес.",
    parameters={
        "type": "object",
        "properties": {
            "recipient": {
                "type": "string",
                "description": "Адрес получателя электронной почты",
            },
            "subject": {
                "type": "string",
                "description": "Тема сообщения",
            },
            "message": {
                "type": "string",
                "description": "Текст сообщения",
            },
        },
        "required": ["recipient", "subject", "message"],
    }
)
    wrapper.add_tool(
        name="calculate_expression",
        func=calculate_expression,
        description="Do mathematical expression evaluation. Add, subtract, multiply, or divide two numbers.",
        parameters={
            "type": "object",
            "properties": {
                "expression": {"type": "string", "description": "Math expression to evaluate",},
            },
            "required": ["expression"],
        },
    )
    wrapper.add_tool(
        name="get_weather",
        func=get_weather,
        description="Get weather information for a given city.",
        parameters={
            "type": "object",
            "properties": {
                "city": {"type": "string", "description": "City name for which to get weather information"},
            },
            "required": ["city"],
        },
    )

    print("Чат с Ollama (введите 'выход' для завершения)\n")

    while True:
        user_input = input("You: ")
        if user_input.lower() in {"выход", "exit"}:
            print("Чат завершен.")
            break

        response = await wrapper.ask(user_input)
        print(f"AI: {response}")

asyncio.run(chat())
