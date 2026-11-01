from locust import HttpUser, task, between
import uuid 
import random

class QuickstartUser(HttpUser):
    
    wait_time = between(1, 2)

    @task
    def user_cycle(self):
        name=str(uuid.uuid4())
        self.client.post("reg", data={'name':name, 'password':'aaa'})
        self.client.post("login", data={'name':name, 'password':'aaa'})
        self.client.get('logout')


