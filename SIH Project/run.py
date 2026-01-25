from app import app_run, socketio
import app.services.socketio_events

app = app_run()

if __name__ == '__main__':
    socketio.run(app, debug =True)