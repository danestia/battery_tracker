import requests

def send_event(event):
    response = requests.post("httpl://placeholder.com/event", json = event)
    return response.status_code == 200