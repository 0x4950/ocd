@socketio.on('my event', namespace='/session_page_namespace')
def handle_message(message):
    """
    This function will be called, when a user(DM) uploads an image.
    It will rebroadcast the image back to all participating the session.
    """
    emit('dis', message, broadcast=True)