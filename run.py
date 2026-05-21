from app import create_app

app = create_app()

if __name__ == '__main__':
    print("Starting AECC RADIUS System on http://localhost:8085...")
    app.run(host='0.0.0.0', port=8085, debug=True)
