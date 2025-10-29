import api
import requests

# Test the app directly
with api.app.test_client() as client:
    response = client.get('/test')
    print('Test route:', response.status_code, response.get_data(as_text=True))
    
    response = client.get('/')
    print('Home route:', response.status_code, response.get_data(as_text=True))
    
    response = client.get('/briefing')
    print('Briefing route:', response.status_code, len(response.get_data(as_text=True)))
