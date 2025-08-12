from app import create_app

# Create an app instance using the factory function
app = create_app()

if __name__ == '__main__':
    # Start the Flask development server
    app.run(port=80,debug=True)