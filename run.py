from waitress import serve
from app import create_app

if __name__ == '__main__':
    # Create an app instance using the factory function
    app = create_app()
    
    # Start the Waitress server
    serve(app, host='0.0.0.0', port=80)