import cv2
import base64
import time

from device import profiler
from camera import CameraBase
from camera.detector import IntruderDetector
from net import AsyncWebsocketClient


__all__ = ['IntruderDetectClient']


class IntruderDetectClient(AsyncWebsocketClient):
    def __init__(self, url):
        AsyncWebsocketClient.__init__(self, url)

        self.camera = CameraBase(0)
        self.camera_detector = IntruderDetector(save_path='output')
        self.camera_detector.register_callback(self.on_detect_event_change)
        self.camera.enable_detector(self.camera_detector)

        self._accept_operation_command = False
        
        self.profiler = profiler.Profiler()
        self.profiler.register_callback(self.on_profiler_update)

        self.register_message_callback(self.on_receive_message)

    def on_profiler_update(self, data):
        self.send(data, 'profiler')

    def test_detect(self, source):
        self.camera.start(source=source)
        self.camera.show()

    def enable_detection(self, operation, feedback=True):
        if operation == 'enable':
            self.camera.start()
        else:
            self.camera.stop()

        print(operation + ' detection')
        if feedback:
            self.send({'operation_type': 'intruder_detection', 'operation': operation}, message_type='operation_feedback')

    def enable_profiler(self, operation, feedback=True):
        if operation == 'enable':
            self.profiler.start()
        else:
            self.profiler.stop()

        print(operation + ' profiler')
        if feedback:
            self.send({'operation_type': 'profiler', 'operation': operation}, message_type='operation_feedback')

    def on_receive_message(self, data):
        message = data.get('message', '')
        message_type = data.get('message_type', '')

        if message_type == 'init':
            self.on_init_message(message)
        elif message_type == 'operation':
            self.on_operation_message(message)

    def on_detect_event_change(self, data):
        path = data.get('path', '')
        intruder_type = data.get('intruder_type', 0)

        if path and intruder_type:
            message = {'intruder_type': intruder_type, 'data_type': 'image',
                       'data_file': None, 'data_file_name': path.replace('output/', '')}
            with open(path, "rb") as f:
                image_data = base64.b64encode(f.read()).decode("utf-8")
                message['data_file'] = image_data
            self.send(message=message, message_type='detect_event')

    def test(self):
        path = 'output/event4_01-58-55.avi'
        message = {'intruder_type': 4, 'data_type': 'image',
                   'data_file': None, 'data_file_name': path.replace('output/', '')}
        with open(path, "rb") as f:
            image_data = base64.b64encode(f.read()).decode("utf-8")
            message['data_file'] = image_data
        self.send(message=message, message_type='detect_event')

    def on_init_message(self, message):
        operation = message.get('operation', '')
        operation_type = message.get('operation_type', '')

        if operation_type == 'profiler':
            self.enable_profiler(operation, feedback=False)
        elif operation_type == 'intruder_detection':
            print("!!")
            # self.enable_detection(operation, feedback=False)

    def on_operation_message(self, message):
        if not self._accept_operation_command:
            return

        operation = message.get('operation', '')
        operation_type = message.get('operation_type', '')

        if operation_type == 'profiler':
            self.enable_profiler(operation)
        elif operation_type == 'intruder_detection':
            self.enable_detection(operation)
        elif operation_type == 'restart':
            self.restart()

    def restart(self):
        print("Received restart message")
        self.send({'operation_type': 'restart', 'operation': ''}, message_type='operation_feedback')


if __name__ == '__main__':
    API_KEY = 'Ff30WhLcvwASASpPWvrV8ZU2E-K_WLkGJeJWy0_3VRw'
    WEBSOCKET_URL = "ws://127.0.0.1:8000/ws/device/{api_key}"
    client = IntruderDetectClient(url=WEBSOCKET_URL.format(api_key=API_KEY))
    client.connect()
    time.sleep(5)
    # client.test()
    client.test_detect('../dataset/crosswalk.avi')
    client.camera.start(0)

    # show function must on main thread
    while True:
        _, frame = client.camera.read(show_time=True, show_fps=True)
        cv2.imshow('Camera {}'.format(0), frame)
        key = cv2.waitKey(1) & 0xff
        if key == 27:  # Esc
            break
