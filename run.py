from app import create_app

# Create an app instance
app = create_app()

if __name__ == '__main__':
    # Used to run the server manually (for local testing)
    app.run(host='0.0.0.0', port=8080)
