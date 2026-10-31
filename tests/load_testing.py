from locust import HttpUser, task, between
import uuid 
import random

class QuickstartUser(HttpUser):
    
    wait_time = between(5, 9)

    @task
    def reg(self):
        name=str(uuid.uuid4())
        self.client.post("reg", data={'name':name, 'password':'aaa'})


