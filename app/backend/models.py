from pydantic import BaseModel,EmailStr
from typing import List,Optional


class User(BaseModel):
    username: str
    email: EmailStr
    password: str
    role: Optional[str] = "User"
    permissions: List[str] = []


class DeviceData(BaseModel):
    Battery_Level: float
    Device_ID: int
    First_Sensor_temperature: float
    Route_From: str
    Route_To: str

class Shipment(BaseModel):
    uname: Optional[str] = None
    uemail: Optional[EmailStr] = None
    ShipNum: int
    RoutDet: str
    Device: str
    PoNum: int
    NdcNum: int
    SeNumOfGoods: str
    ContNum: int
    GoodType: str
    ExpDelDate: str
    DelNum: int
    BatchId: int
    ShipDes: str
