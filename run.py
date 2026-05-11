from flask import Flask
app = Flask(__name__)

@app.route('/')
def index():
    return 'Сервер работает!'

if __name__ == '__main__':
    print("Запускаем сервер...")
    app.run(debug=True, port=5000)