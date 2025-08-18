import json, random, socket, time

try:
    s = socket.socket()
    print("Socket Created")
    s.bind(('', 12345))
    s.listen(3)
    print("Waiting for connections")
    c, addr = s.accept()
    print(f"Connected with {addr}")
 
    
    routes = ['Bengaluru, India','New York, USA', 'Pune, India',  'London, UK', 'Hyderabad, India', 'Louisville, USA']
 
    while True:
        try:
            data = []
            for _ in range(2):  
                route_from = random.choice(routes)
                route_to = random.choice(routes)
 
                while route_from == route_to:
                    route_to = random.choice(routes)
 
                
                device_data = {
                    "Battery_Level": round(random.uniform(2.00, 5.00), 2),
                    "Device_Id": random.randint(1156053075, 1156053080),
                    "First_Sensor_temperature": round(random.uniform(10.0, 40.0), 1),
                    "Route_From": route_from,
                    "Route_To": route_to
                    
                }
                data.append(device_data)
 
         
            userdata = (json.dumps(data) + "\n").encode('utf-8')
            c.send(userdata)
            print(f"Sent data: {userdata.decode('utf-8')}")
            time.sleep(10)
 
        except Exception as e:
            break
 
finally:
    c.close()
   