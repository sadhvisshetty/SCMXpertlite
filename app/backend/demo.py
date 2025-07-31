from pydantic import BaseModel,Field,computed_field
from fastapi import FastAPI

class Todo(BaseModel):
    id:int
    name:str
    price:int
    in_stock:bool


input_data= {'id':100,'name':'sadhvi','price':2000,"in_stock":True}

user=Todo(**input_data)
print(user)



class Booking(BaseModel):
    user_id :int
    room_id:int
    nights:int=Field(ge=1)
    rate_per_night:float
    @computed_field
    @property
    def total_amount(self)->float:#this total_number is considered as an attribute and not as a method,this is the sepciality of computed field..
        return self.nights*self.rate_per_night


    
rooms=Booking(user_id=3,room_id=10,nights=3,rate_per_night=1000)
print(rooms.total_amount)
