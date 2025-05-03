# This file configures separate logging for Flask server

import logging
from logging.handlers import RotatingFileHandler

def setup_server_logging():
    """Set up server log to go to a separate file from chat messages"""
    server_log_handler = RotatingFileHandler(
        'server.log',
        maxBytes=10485760,  # 10MB
        backupCount=5
    )
    server_log_handler.setLevel(logging.INFO)
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    server_log_handler.setFormatter(formatter)
    
    # Flask and Werkzeug loggers
    werkzeug_logger = logging.getLogger('werkzeug')
    werkzeug_logger.setLevel(logging.ERROR)  # Only show errors
    
    flask_logger = logging.getLogger('flask')
    flask_logger.setLevel(logging.ERROR)  # Only show errors
    
    # SocketIO logger
    engineio_logger = logging.getLogger('engineio')
    engineio_logger.setLevel(logging.ERROR)
    
    socketio_logger = logging.getLogger('socketio')
    socketio_logger.setLevel(logging.ERROR)
    
    # Add the handler to all loggers
    werkzeug_logger.addHandler(server_log_handler)
    flask_logger.addHandler(server_log_handler)
    engineio_logger.addHandler(server_log_handler)
    socketio_logger.addHandler(server_log_handler)
    
    return server_log_handler
