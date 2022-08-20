## linebot
### how to use 
- Step 0: Go to main path

- Step 1: Install Python Packages
pip install -r requirements.txt

- Start ngrok https server (default port:8787)
ngrok http 8787

- Step 2: Run main.py 
python main.py
- Step 3: Start InfluxDB service
> sudo systemctl enable influxdb
> sudo systemctl start influxdb
> sudo service influxdb start
Set Port On EC2
Influx 預設開設在 Port: 8086
在 EC2 上開啟 8086



### Directions
- A is first number  
B is second number  
A + B -->A plus B  
A - B -->A minus B  
A * B -->A multiply B  
A / B -->A divided by B  
#note [事件] [+/-] [錢]  
#delete [事件]  
#report   
#sum 還沒做 暫時想不到怎樣處裡 先處理台達專案有空補
